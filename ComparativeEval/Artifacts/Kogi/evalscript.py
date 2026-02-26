import argparse
import logging

from Semantics.istar_processor import read_istar_model
from Semantics.petri_net_processor import read_petri_net
from Semantics.event_mapping_from_csv import read_event_mapping_csv
from Semantics.transition_system import CombinedTransitionSystem

# ---------------- Argument Parsing ----------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Combine an i* goal model with a Petri net and run compliance checks."
    )

    parser.add_argument(
        "--goal-model",
        required=True,
        help="Path to the i* goal model file (e.g., goal_model.txt)"
    )

    parser.add_argument(
        "--petri-net",
        required=True,
        help="Path to the Petri net PNML file (e.g., petri_net.pnml)"
    )

    parser.add_argument(
        "--event-mapping",
        help="Optional CSV file for event mapping (if omitted, default mapping is used)"
    )

    return parser.parse_args()


# ---------------- Logger Setup ----------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)
logger.info("Logger initialized")


# ---------------- Script Execution ----------------

def main():
    args = parse_args()

    goal_model = read_istar_model(args.goal_model)
    logger.info(f"Loaded i* goal model from file: {args.goal_model}")

    petri_net = read_petri_net(args.petri_net)
    logger.info(f"Loaded Petri net model from file: {args.petri_net}")

    if args.event_mapping:
        event_mapping = read_event_mapping_csv(args.event_mapping)
        logger.info(f"Loaded event mapping from CSV file: {args.event_mapping}")
    else:
        event_mapping = petri_net.get_default_event_mapping()
        logger.info("Generated default event mapping from Petri net")

    lts_gm = goal_model.as_transition_system()
    logger.info("Converted goal model into labeled transition system (LTS)")
    logger.info(f"Goal Model LTS reachable states and transitions: {lts_gm.size()}")

    lts_pn = petri_net.as_transition_system()
    logger.info("Converted Petri net into labeled transition system (LTS)")
    logger.info(f"Petri Net LTS reachable states and transitions: {lts_pn.size()}")

    lts_combined = CombinedTransitionSystem(lts_gm, lts_pn, event_mapping)
    logger.info("Created combined transition system from goal model LTS and Petri net LTS")
    logger.info(f"Combined LTS reachable states and transitions: {lts_combined.size()}")

    results = lts_combined.check_stability(goal_model.qualities)
    logger.info("Executed stability check on combined LTS using goal model qualities")
    logger.info(f"Stability: {results[0]}")
    logger.info(f"Counterexamples: {len(results[1])}")

    result = lts_combined.check_weak_compliance(goal_model.qualities)
    logger.info("Executed weak compliance check on combined LTS using goal model qualities")
    logger.info(f"Weak Compliance: {result[0]}")
    logger.info(f"Counterexamples: {len(result[1])}")


if __name__ == "__main__":
    main()

