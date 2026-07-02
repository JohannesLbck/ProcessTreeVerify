#!/usr/bin/env python3
"""
drawast.py - Draw compliance requirement ASTs using graphviz.

Accepts either a JSON requirements file or a CPEE tree XML file and produces
a DOT file + rendered PNG per requirement.

Usage:
    python drawast.py <requirements.json|cpeetree.xml> [--output-dir <dir>] [--format <fmt>]

Dependencies:
    pip install graphviz
"""

import ast
import json
import re
import sys
import os
import argparse
import xml.etree.ElementTree as ET

try:
    from graphviz import Digraph
except ImportError:
    print("Error: 'graphviz' Python package is required. Install with: pip install graphviz")
    sys.exit(1)


CPEE_NS = "http://cpee.org/ns/properties/2.0"


# ---------------------------------------------------------------------------
# Requirement parsers
# ---------------------------------------------------------------------------

def parse_requirements_json(filepath):
    """Parse requirements from a plain JSON file: {"R1": "expr", ...}."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def parse_requirements_xml(filepath):
    """Parse requirements from a CPEE tree XML file.

    The requirements live in <attributes><requirements>...</requirements></attributes>
    and use Ruby hash syntax (=>) instead of JSON (:).
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Try with the CPEE namespace first, then without
    req_elem = root.find(f'.//{{{CPEE_NS}}}requirements')
    if req_elem is None:
        req_elem = root.find('.//requirements')

    if req_elem is None or not req_elem.text:
        raise ValueError("No <requirements> element found in the XML file.")

    req_text = req_elem.text.strip()
    # Ruby hash syntax uses => ; convert to JSON colon
    req_text = re.sub(r'=>', ':', req_text)
    return json.loads(req_text)


# ---------------------------------------------------------------------------
# AST → graphviz
# ---------------------------------------------------------------------------

# Visual style for requirement-expression nodes
_STYLE = {
    "boolop":   dict(shape="diamond", style="filled", fillcolor="lightyellow"),
    "unaryop":  dict(shape="diamond", style="filled", fillcolor="lightyellow"),
    "call":     dict(shape="box",     style="filled", fillcolor="lightblue"),
    "constant": dict(shape="ellipse", style="filled", fillcolor="lightgreen"),
    "name":     dict(shape="ellipse", style="filled", fillcolor="lightgreen"),
    "default":  dict(shape="plaintext"),
}

# Visual styles for implementation body nodes (--full-tree mode)
_IMPL_STYLES = {
    "if":      dict(shape="diamond", style="filled", fillcolor="#ffe699",  fontsize="9"),
    "for":     dict(shape="diamond", style="filled", fillcolor="#c9e8f0",  fontsize="9"),
    "while":   dict(shape="diamond", style="filled", fillcolor="#c9e8f0",  fontsize="9"),
    "return":  dict(shape="box",     style="filled", fillcolor="#ffb3b3",  fontsize="9"),
    "assign":  dict(shape="box",     fontsize="9"),
    "expr":    dict(shape="box",     style="dashed", fontsize="9"),
    "try":     dict(shape="box",     style="filled", fillcolor="#e0d0f0",  fontsize="9"),
    "default": dict(shape="box",     fontsize="9"),
}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _safe_unparse(node, max_len=55):
    """Unparse an AST node to a string, replacing newlines and truncating."""
    try:
        s = ast.unparse(node)
    except Exception:
        s = type(node).__name__
    s = s.replace("\n", " ")
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _is_docstring(node):
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _is_logger_call(node):
    """Return True if *node* is an ``Expr`` statement that calls ``logger.*``."""
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "logger"
    )


def load_cp_function_asts(av_path):
    """Parse *av_path* (annotated_verification.py) and return
    ``{func_name: ast.FunctionDef}`` for every top-level function.
    """
    if not os.path.exists(av_path):
        print(f"[WARN] Implementation file not found: {av_path}")
        return {}
    with open(av_path, encoding="utf-8") as f:
        source = f.read()
    module = ast.parse(source)
    return {
        n.name: n
        for n in ast.walk(module)
        if isinstance(n, ast.FunctionDef)
    }


# Aliases from VERIFICATION_FUNCTIONS in verificationAST.py:
# older requirement names that map to the canonical implementation name.
_ALIAS_MAP = {
    "data_value_alternative":                  "condition",
    "data_value_alternative_directly_follows": "condition_directly_follows",
    "data_value_alternative_eventually_follows": "condition_eventually_follows",
}


# ---------------------------------------------------------------------------
# Implementation-body renderer (used by --full-tree mode)
# ---------------------------------------------------------------------------

def _render_body_to_graph(stmts, g, counter, prefix, parent_id=None, edge_label="", skip_logs=False):
    """Render *stmts* as a sequential chain in graph *g*.

    If *parent_id* is given the first statement gets an edge from it labelled
    *edge_label*.  When *skip_logs* is True, ``logger.*`` calls are omitted.
    Returns the node-id of the first rendered statement or ``None`` when all
    statements were skipped.
    """
    prev_id = parent_id
    first_id = None
    for stmt in stmts:
        if _is_docstring(stmt):
            continue
        if skip_logs and _is_logger_call(stmt):
            continue
        stmt_id = _render_stmt_to_graph(stmt, g, counter, prefix, skip_logs=skip_logs)
        if prev_id is not None:
            lbl = edge_label if (prev_id == parent_id) else ""
            g.edge(prev_id, stmt_id, label=lbl)
        prev_id = stmt_id
        if first_id is None:
            first_id = stmt_id
    return first_id


def _render_stmt_to_graph(node, g, counter, prefix, skip_logs=False):
    """Render one Python AST statement node into graph *g*.

    Handles ``If``, ``For``, ``While``, ``Return``, ``Assign``, ``Expr``,
    ``Try``, ``Continue``, ``Break``, ``Pass``, and a generic fallback.
    *skip_logs* is forwarded to recursive body renderings.
    Returns the graphviz node-id.
    """
    node_id = f"{prefix}s{counter[0]}"
    counter[0] += 1

    if isinstance(node, ast.If):
        cond_str = _safe_unparse(node.test, 50)
        g.node(node_id, label=f"if {cond_str}", **_IMPL_STYLES["if"])
        if node.body:
            _render_body_to_graph(node.body, g, counter, prefix, node_id, "T", skip_logs)
        if node.orelse:
            _render_body_to_graph(node.orelse, g, counter, prefix, node_id, "F", skip_logs)

    elif isinstance(node, ast.For):
        label = (
            f"for {_safe_unparse(node.target, 20)} "
            f"in {_safe_unparse(node.iter, 30)}"
        )
        g.node(node_id, label=label, **_IMPL_STYLES["for"])
        if node.body:
            _render_body_to_graph(node.body, g, counter, prefix, node_id, skip_logs=skip_logs)

    elif isinstance(node, ast.While):
        g.node(
            node_id,
            label=f"while {_safe_unparse(node.test, 50)}",
            **_IMPL_STYLES["while"],
        )
        if node.body:
            _render_body_to_graph(node.body, g, counter, prefix, node_id, skip_logs=skip_logs)

    elif isinstance(node, ast.Return):
        val_str = _safe_unparse(node.value, 50) if node.value else ""
        g.node(node_id, label=f"return {val_str}", **_IMPL_STYLES["return"])

    elif isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
        g.node(node_id, label=_safe_unparse(node, 60), **_IMPL_STYLES["assign"])

    elif isinstance(node, ast.Expr):
        g.node(node_id, label=_safe_unparse(node.value, 60), **_IMPL_STYLES["expr"])

    elif isinstance(node, ast.Try):
        g.node(node_id, label="try", **_IMPL_STYLES["try"])
        if node.body:
            _render_body_to_graph(node.body, g, counter, prefix, node_id, skip_logs=skip_logs)
        for handler in node.handlers:
            exc = _safe_unparse(handler.type, 30) if handler.type else "*"
            h_id = f"{prefix}s{counter[0]}"
            counter[0] += 1
            g.node(h_id, label=f"except {exc}", **_IMPL_STYLES["try"])
            g.edge(node_id, h_id)
            if handler.body:
                _render_body_to_graph(handler.body, g, counter, prefix, h_id, skip_logs=skip_logs)

    elif isinstance(node, (ast.Continue, ast.Break, ast.Pass)):
        g.node(node_id, label=type(node).__name__.lower(), **_IMPL_STYLES["default"])

    else:
        try:
            label = _safe_unparse(node, 60)
        except Exception:
            label = type(node).__name__
        g.node(node_id, label=label, **_IMPL_STYLES["default"])

    return node_id


# ---------------------------------------------------------------------------
# Requirement-expression AST renderer
# ---------------------------------------------------------------------------

def _ast_to_dot(node, graph, counter, full_tree=False, cp_funcs=None, skip_logs=False):
    """Recursively translate a Python AST node into graphviz nodes/edges.

    When *full_tree* is True and *cp_funcs* contains the function's AST,
    each compliance-pattern call is expanded with a cluster subgraph showing
    its complete implementation body from annotated_verification.py.
    When *skip_logs* is True, ``logger.*`` calls are omitted from those clusters.

    Returns the graphviz node-id of *node*.
    """
    node_id = f"n{counter[0]}"
    counter[0] += 1

    if isinstance(node, ast.Expression):
        # Transparent wrapper – recurse into body, reuse its id
        return _ast_to_dot(node.body, graph, counter, full_tree, cp_funcs, skip_logs)

    elif isinstance(node, ast.BoolOp):
        op_label = "and" if isinstance(node.op, ast.And) else "or"
        graph.node(node_id, label=op_label, **_STYLE["boolop"])
        for value in node.values:
            child_id = _ast_to_dot(value, graph, counter, full_tree, cp_funcs, skip_logs)
            graph.edge(node_id, child_id)

    elif isinstance(node, ast.UnaryOp):
        op_label = "not" if isinstance(node.op, ast.Not) else type(node.op).__name__
        graph.node(node_id, label=op_label, **_STYLE["unaryop"])
        child_id = _ast_to_dot(node.operand, graph, counter, full_tree, cp_funcs, skip_logs)
        graph.edge(node_id, child_id)

    elif isinstance(node, ast.Call):
        func_name = node.func.id if isinstance(node.func, ast.Name) else repr(node.func)
        graph.node(node_id, label=func_name, **_STYLE["call"])
        for arg in node.args:
            child_id = _ast_to_dot(arg, graph, counter, full_tree, cp_funcs, skip_logs)
            graph.edge(node_id, child_id)
        # keyword arguments (e.g. timeout=900)
        for kw in node.keywords:
            kw_label = f"{kw.arg}=" if kw.arg else "**"
            kw_id = f"n{counter[0]}"
            counter[0] += 1
            graph.node(kw_id, label=kw_label, shape="box", style="dashed")
            graph.edge(node_id, kw_id)
            val_id = _ast_to_dot(kw.value, graph, counter, full_tree, cp_funcs, skip_logs)
            graph.edge(kw_id, val_id)

        # --full-tree / --full-tree-with-logs: expand body as a cluster subgraph
        resolved_name = _ALIAS_MAP.get(func_name, func_name)
        if full_tree and cp_funcs and resolved_name in cp_funcs:
            func_def = cp_funcs[resolved_name]
            body = [s for s in func_def.body if not _is_docstring(s)]
            if body:
                cluster_name = f"cluster_impl_{resolved_name}_{node_id}"
                first_stmt_id = [None]  # mutable cell accessible inside with-block
                impl_label = (
                    f"impl: {resolved_name} (alias: {func_name})"
                    if resolved_name != func_name
                    else f"impl: {func_name}"
                )

                with graph.subgraph(name=cluster_name) as sg:
                    sg.attr(
                        label=impl_label,
                        style="dashed",
                        color="gray50",
                        fontsize="10",
                        fontname="Helvetica",
                    )
                    sg.attr("node", fontname="Helvetica")
                    prefix = f"i{node_id}_"
                    first_stmt_id[0] = _render_body_to_graph(
                        body, sg, counter, prefix, skip_logs=skip_logs
                    )

                if first_stmt_id[0] is not None:
                    graph.edge(
                        node_id, first_stmt_id[0],
                        style="dashed", color="gray50", label="impl",
                    )

    elif isinstance(node, ast.Constant):
        graph.node(node_id, label=str(node.value), **_STYLE["constant"])

    elif isinstance(node, ast.Name):
        graph.node(node_id, label=node.id, **_STYLE["name"])

    else:
        graph.node(node_id, label=type(node).__name__, **_STYLE["default"])

    return node_id


# ---------------------------------------------------------------------------
# Per-requirement drawing
# ---------------------------------------------------------------------------

def draw_requirement(req_id, expression, output_dir, render_format,
                     full_tree=False, cp_funcs=None, skip_logs=False):
    """Parse *expression* as a Python AST and write DOT + rendered image.

    When *full_tree* is True each top-level compliance-pattern call is
    expanded with a cluster showing its implementation from
    annotated_verification.py (loaded into *cp_funcs*).
    When *skip_logs* is True, ``logger.*`` calls are omitted from those clusters.
    """
    expression = expression.strip()
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        print(f"  [WARN] Could not parse {req_id}: {exc}")
        return

    # Truncate long expressions for the graph title
    title_expr = expression if len(expression) <= 200 else expression[:197] + "..."
    if full_tree and skip_logs:
        suffix = " [full tree]"
    elif full_tree:
        suffix = " [full tree + logs]"
    else:
        suffix = ""
    graph = Digraph(comment=f"AST for {req_id}")
    graph.attr(
        label=f"{req_id}{suffix}: {title_expr}",
        labelloc="t",
        fontsize="11",
        fontname="Helvetica",
    )
    graph.attr("node", fontname="Helvetica", fontsize="10")
    graph.attr("edge", fontname="Helvetica", fontsize="9")

    counter = [0]
    _ast_to_dot(tree, graph, counter, full_tree=full_tree, cp_funcs=cp_funcs or {}, skip_logs=skip_logs)

    # Save .dot file
    dot_path = os.path.join(output_dir, f"{req_id}.dot")
    with open(dot_path, "w", encoding="utf-8") as f:
        f.write(graph.source)

    # Render (e.g. to PNG/PDF)
    render_base = os.path.join(output_dir, req_id)
    try:
        graph.render(render_base, format=render_format, cleanup=True)
        rendered = f"{render_base}.{render_format}"
        print(f"  Saved: {dot_path}  |  {rendered}")
    except Exception as exc:
        print(f"  Saved: {dot_path}  (rendering failed: {exc})")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_DEFAULT_AV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "python_code", "annotated_verification.py",
)


def main():
    parser = argparse.ArgumentParser(
        description="Draw compliance requirement ASTs using graphviz."
    )
    parser.add_argument(
        "input",
        help="Path to a .json requirements file or a CPEE tree .xml file.",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help=(
            "Directory to save .dot and rendered files. "
            "Defaults to <input_stem>_asts/ (or <input_stem>_asts_full/ with --full-tree) "
            "next to the input file."
        ),
    )
    parser.add_argument(
        "--format", "-f",
        default="png",
        dest="fmt",
        help="Graphviz output format (png, pdf, svg, …). Default: png.",
    )
    parser.add_argument(
        "--full-tree",
        action="store_true",
        default=False,
        help=(
            "Expand each compliance-pattern call with its complete implementation "
            "AST from annotated_verification.py, omitting logger calls."
        ),
    )
    parser.add_argument(
        "--full-tree-with-logs",
        action="store_true",
        default=False,
        help=(
            "Like --full-tree but also includes logger.info/warning/… calls "
            "in the implementation clusters."
        ),
    )
    parser.add_argument(
        "--av-path",
        default=_DEFAULT_AV_PATH,
        metavar="PATH",
        help=(
            "Path to annotated_verification.py used by --full-tree / "
            "--full-tree-with-logs. "
            f"Default: {_DEFAULT_AV_PATH}"
        ),
    )
    args = parser.parse_args()

    filepath = os.path.abspath(args.input)
    if not os.path.exists(filepath):
        print(f"Error: file not found: {filepath}")
        sys.exit(1)

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".json":
        requirements = parse_requirements_json(filepath)
    elif ext == ".xml":
        requirements = parse_requirements_xml(filepath)
    else:
        print(f"Error: unsupported extension '{ext}'. Provide a .json or .xml file.")
        sys.exit(1)

    # Resolve mode flags
    full_tree = args.full_tree or args.full_tree_with_logs
    skip_logs = args.full_tree and not args.full_tree_with_logs

    # Load implementation ASTs when an expansion flag is requested
    cp_funcs = {}
    if full_tree:
        cp_funcs = load_cp_function_asts(args.av_path)
        if cp_funcs:
            print(f"Loaded {len(cp_funcs)} function ASTs from {args.av_path}")

    # Resolve output directory
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
    else:
        stem = os.path.splitext(os.path.basename(filepath))[0]
        if args.full_tree_with_logs:
            dir_suffix = "_asts_full_with_logs"
        elif args.full_tree:
            dir_suffix = "_asts_full"
        else:
            dir_suffix = "_asts"
        output_dir = os.path.join(os.path.dirname(filepath), f"{stem}{dir_suffix}")

    os.makedirs(output_dir, exist_ok=True)
    print(f"Input:      {filepath}")
    print(f"Output dir: {output_dir}")
    print(f"Format:     {args.fmt}")
    print(f"Full tree:  {full_tree}  (skip_logs={skip_logs})")
    print(f"Requirements found: {len(requirements)}\n")

    for req_id, expression in requirements.items():
        print(f"Processing {req_id}: {expression.strip()[:60]}{'...' if len(expression.strip()) > 60 else ''}")
        draw_requirement(
            req_id, expression, output_dir, args.fmt,
            full_tree=full_tree, cp_funcs=cp_funcs, skip_logs=skip_logs,
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
