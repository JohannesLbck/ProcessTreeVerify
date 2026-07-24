import ast
import xml.etree.ElementTree as ET
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
import logging

logger = logging.getLogger(__name__)

# Lazily initialize the model in-process to avoid CUDA/fork initialization issues.
_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    return _MODEL


SIMILARITY_THRESHOLD = 0.6

# Argument indices (including leading tree argument) that represent activity labels.
LABEL_ARGUMENTS = {
    'exists': [1],
    'absence': [1],
    'loop': [1],
    'directly_follows': [1, 2],
    'leads_to': [1, 2],
    'precedence': [1, 2],
    'leads_to_absence': [1, 2],
    'precedence_absence': [1, 2],
    'parallel': [1, 2],
    'executed_by': [1],
    'executed_by_return': [1],
    'recurring': [1],
    'timed_alternative': [1, 2],
    'min_time_between': [1, 2],
    'by_due_date': [1],
    'max_time_between': [1, 2],
    'activity_sends': [1],
    'activity_receives': [1],
    'condition_directly_follows': [2],
    'condition_eventually_follows': [2],
    'data_leads_to_absence': [2],
    'failure_directly_follows': [1, 2],
    'failure_eventually_follows': [1, 2],
}

# Special process tree labels that should never be replaced with semantic matching
# These are reserved system elements from annotated_verification.py exists() method
SPECIAL_LABELS = {
    'end activity',
    'start activity',
    'terminate',
}


def _best_label_match(candidate_label, labels, tree_label_embeddings, verbose=False):
    """Return best semantic label match or None if no confident replacement exists."""
    if not isinstance(candidate_label, str) or not candidate_label.strip():
        return None
    
    # Skip special process tree labels that should never be replaced
    if candidate_label.lower() in SPECIAL_LABELS:
        return None

    quoted_embedding = _get_model().encode(candidate_label)
    similarities = cos_sim(quoted_embedding, tree_label_embeddings)[0]

    if verbose:
        similarity_list = [
            (label, float(similarities[i].item()))
            for i, label in enumerate(labels)
        ]
        logger.info(f"Similarity scores for '{candidate_label}': {similarity_list}")

    best_idx = similarities.argmax()
    best_similarity = similarities[best_idx].item()
    best_match = labels[best_idx]

    # Log a warning if multiple candidates are above the threshold
    above_threshold = [label for i, label in enumerate(labels) if similarities[i].item() > SIMILARITY_THRESHOLD]
    if len(above_threshold) > 1:
        logger.warning(f"Multiple candidates found for label '{candidate_label}': {above_threshold}")

    if best_similarity > SIMILARITY_THRESHOLD:
        logger.info(f"Replace '{candidate_label}' with semantically similar label '{best_match}'")
        return best_match

    # Log an error if no match is found
    logger.error(f"No confident match found for label '{candidate_label}'")
    return None


class LabelReplacer(ast.NodeTransformer):
    def __init__(self, labels, tree_label_embeddings, verbose=False):
        self.labels = labels
        self.tree_label_embeddings = tree_label_embeddings
        self.verbose = verbose

    def visit_Call(self, node: ast.Call):
        visited = self.generic_visit(node)
        if not isinstance(visited, ast.Call):
            return visited
        node = visited

        if not isinstance(node.func, ast.Name):
            return node

        label_indices = LABEL_ARGUMENTS.get(node.func.id, [])
        for arg_index in label_indices:
            if arg_index >= len(node.args):
                continue

            arg = node.args[arg_index]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                try:
                    replacement = _best_label_match(
                        arg.value,
                        self.labels,
                        self.tree_label_embeddings,
                        verbose=self.verbose,
                    )
                except Exception:
                    replacement = None
                if replacement is not None:
                    node.args[arg_index] = ast.copy_location(ast.Constant(value=replacement), arg)

        return node


def extract_labels(xml):
    """
    Extract all activity labels from a CPEE XML tree and compute their embeddings.
    Labels are located in call > parameters > label elements.
    
    Args:
        xml: XML string or ElementTree to extract labels from
        
    Returns:
        Dict with 'labels' (list of label strings) and 'embeddings' (precomputed embeddings)
    """
    try:
        if isinstance(xml, str):
            root = ET.fromstring(xml)
        else:
            root = xml
    except Exception as e:
        return {'labels': [], 'embeddings': None}
    
    labels = []

    def local_name(tag):
        return tag.split('}', 1)[-1] if '}' in tag else tag

    # Find all 'call' elements and extract labels from direct parameters/label children.
    # This is namespace-safe for tags like {ns}call.
    for call_elem in root.iter():
        if local_name(call_elem.tag) != 'call':
            continue
        for param_elem in list(call_elem):
            if local_name(param_elem.tag) != 'parameters':
                continue
            for label_elem in list(param_elem):
                if local_name(label_elem.tag) != 'label':
                    continue
                if label_elem.text:
                    label_text = label_elem.text.strip()
                    if label_text:
                        labels.append(label_text)
    
    # Precompute embeddings for all labels
    embeddings = _get_model().encode(labels) if labels else None
    
    return {'labels': labels, 'embeddings': embeddings}


def replace_labels(req, labels_data, verbose=False):
    """
    Replace activity labels in a requirement AST with semantically similar labels from the tree.
    Uses precomputed sentence transformer embeddings and AST traversal to only rewrite
    function arguments that represent activity labels.
    
    Args:
        req: String containing the requirement/AST expression
        labels_data: Dict with 'labels' (list of label strings) and 'embeddings' (precomputed embeddings)
        
    Returns:
        Modified requirement with semantically matched labels
    """
    if not labels_data or not labels_data.get('labels'):
        return req
    
    labels = labels_data['labels']
    tree_label_embeddings = labels_data['embeddings']
    
    if tree_label_embeddings is None:
        return req
    
    try:
        expr = ast.parse(req, mode='eval')
    except Exception:
        return req

    transformed = LabelReplacer(labels, tree_label_embeddings, verbose=verbose).visit(expr)
    ast.fix_missing_locations(transformed)
    return ast.unparse(transformed)