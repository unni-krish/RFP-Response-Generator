import os
import json
import logging
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END

# Import the agents
from app.agents.A1_Intake import process_folder as intake_process_folder
from app.agents.A2_Extract import A2ExtractAgent
from app.agents.A3_Requirement import A3RequirementAgent
from app.agents.A4_Compliance import A4ComplianceAgent
from app.agents.A5_Solution import A5SolutionAgent
from app.agents.A5_1_ArchitectureGenerator import A5_1ArchitectureGeneratorAgent
from app.utils.config import load_config

config = load_config()
paths_config = config.get("paths", {})
INPUT_FOLDER = paths_config.get("input_folder", "input")
OUTPUT_FOLDER = paths_config.get("output_folder", "output")

orchestrator_config = config.get("orchestrator", {})
DEFAULT_VISION_MODEL = orchestrator_config.get("default_vision_model", "gpt-4o")
DEFAULT_TEXT_MODEL = orchestrator_config.get("default_text_model", "gpt-4o")
# Config-level testing flag — can be overridden per-call via run_pipeline(testing_mode=False)
CONFIG_TESTING_MODE = orchestrator_config.get("testing", False)

LOGS_FOLDER = paths_config.get("logs_folder", "logs")

import sys
try:
    # Project root is one level up from app/
    base_dir_global = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    base_dir_global = os.getcwd()
logs_dir = os.path.join(base_dir_global, LOGS_FOLDER)

os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, "orchestrator.log")

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Orchestrator")

# 1. Define State
class OrchestratorState(TypedDict):
    input_folder: str
    intake_results: List[Dict[str, Any]]
    extract_report: str
    requirements_report: str
    compliance_report: str
    solution_report: str
    ppt_structure: dict
    status: str
    testing_mode: bool   # runtime override — False forces fresh run even if config says true

def load_previous_state() -> dict:
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        base_dir = os.getcwd()
    output_dir = os.path.join(base_dir, OUTPUT_FOLDER)
    final_state_path = os.path.join(output_dir, "final_state.json")
    
    if os.path.exists(final_state_path):
        try:
            with open(final_state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load previous state: {e}")
    return {}

# 2. Define Nodes
def intake_node(state: OrchestratorState) -> OrchestratorState:
    if state.get("intake_results"):
        logger.info("Using provided intake_results from state payload")
        state["status"] = "INTAKE_COMPLETE"
        return state

    folder = state["input_folder"]
    TESTING_MODE = state.get("testing_mode", CONFIG_TESTING_MODE)
    
    if TESTING_MODE:
        prev_state = load_previous_state()
        prev_results = prev_state.get("intake_results")
        if prev_results and prev_state.get("status") not in ["INTAKE_FAILED", "INITIALIZED"]:
            logger.info("TESTING MODE: Using cached intake_results from final_state.json")
            state["intake_results"] = prev_results
            state["status"] = "INTAKE_COMPLETE"
            return state

    logger.info(f"--- INTAKE NODE: Validating folder '{folder}' ---")
    
    # Run A1 Agent
    try:
        results = intake_process_folder(folder)
        state["intake_results"] = results
        state["status"] = "INTAKE_COMPLETE"
    except Exception as e:
        logger.error(f"Intake failed: {e}")
        state["intake_results"] = []
        state["status"] = "INTAKE_FAILED"
        
    return state

def extraction_node(state: OrchestratorState) -> OrchestratorState:
    if state.get("extract_report") and not state.get("extract_report").startswith("Extraction failed"):
        logger.info("Using provided extract_report from state payload")
        state["status"] = "EXTRACTION_COMPLETE"
        return state

    folder = state["input_folder"]
    TESTING_MODE = state.get("testing_mode", CONFIG_TESTING_MODE)
    
    if TESTING_MODE:
        prev_state = load_previous_state()
        prev_report = prev_state.get("extract_report")
        if prev_report and prev_state.get("status") not in ["INTAKE_FAILED", "EXTRACTION_FAILED", "INITIALIZED"] and not prev_report.startswith("Extraction failed"):
            logger.info("TESTING MODE: Using cached extract_report from final_state.json")
            state["extract_report"] = prev_report
            state["status"] = "EXTRACTION_COMPLETE"
            return state

    logger.info(f"--- EXTRACTION NODE: Processing valid documents in '{folder}' ---")
    
    # Run A2 Agent
    try:
        agent = A2ExtractAgent(vision_model=DEFAULT_VISION_MODEL, text_model=DEFAULT_TEXT_MODEL)
        report = agent.generate_report(folder)
        state["extract_report"] = report
        state["status"] = "EXTRACTION_COMPLETE"
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        state["extract_report"] = f"Extraction failed with error: {e}"
        state["status"] = "EXTRACTION_FAILED"
        
    return state

def requirement_node(state: OrchestratorState) -> OrchestratorState:
    if state.get("status") in ["EXTRACTION_FAILED", "INTAKE_FAILED"]:
        return state
        
    if state.get("requirements_report"):
        logger.info("Using provided requirements_report from state payload")
        state["status"] = "REQUIREMENT_COMPLETE"
        return state

    TESTING_MODE = state.get("testing_mode", CONFIG_TESTING_MODE)
    
    if TESTING_MODE:
        prev_state = load_previous_state()
        prev_reqs = prev_state.get("requirements_report")
        if prev_reqs and prev_state.get("status") not in ["INTAKE_FAILED", "EXTRACTION_FAILED", "REQUIREMENT_FAILED", "INITIALIZED"]:
            logger.info("TESTING MODE: Using cached requirements_report from final_state.json")
            state["requirements_report"] = prev_reqs
            state["status"] = "REQUIREMENT_COMPLETE"
            return state

    logger.info("--- REQUIREMENT NODE: Extracting requirements from final report ---")
    try:
        agent = A3RequirementAgent()
        reqs = agent.extract_requirements(state.get("extract_report", ""))
        state["requirements_report"] = reqs
        state["status"] = "REQUIREMENT_COMPLETE"
    except Exception as e:
        logger.error(f"Requirement extraction failed: {e}")
        state["requirements_report"] = ""
        state["status"] = "REQUIREMENT_FAILED"
        
    return state

def compliance_node(state: OrchestratorState) -> OrchestratorState:
    if state.get("status") in ["EXTRACTION_FAILED", "INTAKE_FAILED", "REQUIREMENT_FAILED"]:
        return state

    if state.get("compliance_report") and not state.get("compliance_report").startswith("Compliance validation failed"):
        logger.info("Using provided compliance_report from state payload")
        state["status"] = "COMPLIANCE_COMPLETE"
        return state

    TESTING_MODE = state.get("testing_mode", CONFIG_TESTING_MODE)
    
    if TESTING_MODE:
        prev_state = load_previous_state()
        prev_comp = prev_state.get("compliance_report")
        if prev_comp and prev_state.get("status") not in ["INTAKE_FAILED", "EXTRACTION_FAILED", "REQUIREMENT_FAILED", "COMPLIANCE_FAILED", "INITIALIZED"]:
            logger.info("TESTING MODE: Using cached compliance_report from final_state.json")
            state["compliance_report"] = prev_comp
            state["status"] = "COMPLIANCE_COMPLETE"
            return state

    logger.info("--- COMPLIANCE NODE: Validating requirements against compliance frameworks ---")
    try:
        agent = A4ComplianceAgent()
        reqs_text = state.get("requirements_report", "")
        report = agent.validate_requirements(reqs_text)
        state["compliance_report"] = report
        state["status"] = "COMPLIANCE_COMPLETE"
    except Exception as e:
        logger.error(f"Compliance validation failed: {e}")
        state["compliance_report"] = f"Compliance validation failed with error: {e}"
        state["status"] = "COMPLIANCE_FAILED"
        
    return state

def solution_node(state: OrchestratorState) -> OrchestratorState:
    if state.get("status") in ["EXTRACTION_FAILED", "INTAKE_FAILED", "REQUIREMENT_FAILED", "COMPLIANCE_FAILED"]:
        return state

    if state.get("solution_report") and not state.get("solution_report").startswith("Solution generation failed"):
        logger.info("Using provided solution_report from state payload")
        state["status"] = "SOLUTION_COMPLETE"
        return state

    TESTING_MODE = state.get("testing_mode", CONFIG_TESTING_MODE)
    
    if TESTING_MODE:
        prev_state = load_previous_state()
        prev_sol = prev_state.get("solution_report")
        if prev_sol and prev_state.get("status") not in ["INTAKE_FAILED", "EXTRACTION_FAILED", "REQUIREMENT_FAILED", "COMPLIANCE_FAILED", "SOLUTION_FAILED", "INITIALIZED"]:
            logger.info("TESTING MODE: Using cached solution_report from final_state.json")
            state["solution_report"] = prev_sol
            state["status"] = "SOLUTION_COMPLETE"
            return state

    logger.info("--- SOLUTION NODE: Generating solution architecture recommendation ---")
    try:
        agent = A5SolutionAgent()
        reqs_text = state.get("requirements_report", "")
        comp_text = state.get("compliance_report", "")
        report = agent.generate_solution(reqs_text, comp_text)
        state["solution_report"] = report
        state["status"] = "SOLUTION_COMPLETE"
    except Exception as e:
        logger.error(f"Solution generation failed: {e}")
        state["solution_report"] = f"Solution generation failed with error: {e}"
        state["status"] = "SOLUTION_FAILED"
        
    return state

def ppt_node(state: OrchestratorState) -> OrchestratorState:
    if state.get("status") in ["EXTRACTION_FAILED", "INTAKE_FAILED", "REQUIREMENT_FAILED", "COMPLIANCE_FAILED", "SOLUTION_FAILED"]:
        return state

    if state.get("ppt_structure"):
        logger.info("Using provided ppt_structure from state payload")
        state["status"] = "PPT_COMPLETE"
        return state

    TESTING_MODE = state.get("testing_mode", CONFIG_TESTING_MODE)
    
    if TESTING_MODE:
        prev_state = load_previous_state()
        prev_ppt = prev_state.get("ppt_structure")
        if prev_ppt and prev_state.get("status") not in ["INTAKE_FAILED", "EXTRACTION_FAILED", "REQUIREMENT_FAILED", "COMPLIANCE_FAILED", "SOLUTION_FAILED", "PPT_FAILED", "INITIALIZED"]:
            logger.info("TESTING MODE: Using cached ppt_structure from final_state.json")
            state["ppt_structure"] = prev_ppt
            state["status"] = "PPT_COMPLETE"
            return state

    logger.info("--- PPT NODE: Generating Architecture Deck ---")
    try:
        agent = A5_1ArchitectureGeneratorAgent()
        sol = state.get("solution_report", "")

        # Resolve output directory so diagram PNG lands alongside other outputs
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        except NameError:
            base_dir = os.getcwd()
        out_dir = os.path.join(base_dir, OUTPUT_FOLDER)
        os.makedirs(out_dir, exist_ok=True)

        ppt_json = agent.generate_ppt_structure(sol, output_dir=out_dir)
        state["ppt_structure"] = ppt_json
        state["status"] = "PPT_COMPLETE"
    except Exception as e:
        logger.error(f"PPT generation failed: {e}")
        state["ppt_structure"] = {}
        state["status"] = "PPT_FAILED"
        
    return state


# 3. Define Conditional Routing
def route_after_intake(state: OrchestratorState) -> str:
    results = state.get("intake_results", [])
    
    if not results:
        logger.info("Routing logic: No files found to process. Ending process early.")
        return END
        
    invalid_files = [r for r in results if r.get("status") == "INVALID"]
    
    if len(invalid_files) > 0:
        logger.warning(f"Routing logic: Found {len(invalid_files)} INVALID file(s). Halting process and skipping extraction.")
        return END
    else:
        logger.info("Routing logic: All files are VALID. Proceeding to extraction.")
        return "extraction_node"

# 4. Build the Graph
def build_orchestrator():
    graph_builder = StateGraph(OrchestratorState)
    
    # Add Nodes
    graph_builder.add_node("intake_node", intake_node)
    graph_builder.add_node("extraction_node", extraction_node)
    graph_builder.add_node("requirement_node", requirement_node)
    graph_builder.add_node("compliance_node", compliance_node)
    graph_builder.add_node("solution_node", solution_node)
    graph_builder.add_node("ppt_node", ppt_node)
    
    # Add Edges
    graph_builder.add_edge(START, "intake_node")
    graph_builder.add_conditional_edges(
        "intake_node",
        route_after_intake,
        {
            "extraction_node": "extraction_node",
            END: END
        }
    )
    graph_builder.add_edge("extraction_node", "requirement_node")
    graph_builder.add_edge("requirement_node", "compliance_node")
    graph_builder.add_edge("compliance_node", "solution_node")
    graph_builder.add_edge("solution_node", "ppt_node")
    graph_builder.add_edge("ppt_node", END)
    
    # Compile
    return graph_builder.compile()

def run_pipeline(input_folder: str, output_folder: str, testing_mode: bool = None, provided_state: dict = None) -> tuple:
    """
    Run the orchestrator pipeline on the given input folder and return a tuple: (pptx_path, final_state).
    
    Args:
        input_folder: Path to folder containing input documents.
        output_folder: Path to write output files.
        testing_mode: If explicitly set (True/False), overrides the params.yml `testing` flag.
                      Pass False from the API to always process uploaded files fresh.
                      Defaults to None (uses params.yml value).
        provided_state: Optional dictionary containing state values to skip steps.
    """
    # Resolve effective testing mode: explicit arg wins over config
    effective_testing_mode = CONFIG_TESTING_MODE if testing_mode is None else testing_mode
    if provided_state is None:
        provided_state = {}
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    logger.info("Initializing LangGraph Orchestrator...")
    orchestrator = build_orchestrator()
    
    initial_state = {
        "input_folder": input_folder,
        "intake_results": provided_state.get("intake_results", []),
        "extract_report": provided_state.get("extract_report", ""),
        "requirements_report": provided_state.get("requirements_report", ""),
        "compliance_report": provided_state.get("compliance_report", ""),
        "solution_report": provided_state.get("solution_report", ""),
        "ppt_structure": provided_state.get("ppt_structure", {}),
        "status": provided_state.get("status", "INITIALIZED"),
        "testing_mode": effective_testing_mode
    }
    
    logger.info(f"Running Orchestrator on folder: {input_folder}")
    final_state = orchestrator.invoke(initial_state)
    
    logger.info(f"Final Status: {final_state.get('status')}")
    
    # Save final_state.json to output directory
    final_state_path = os.path.join(output_folder, "final_state.json")
    
    with open(final_state_path, "w", encoding="utf-8") as f:
        f.write("{\n")
        keys = list(final_state.keys())
        for i, k in enumerate(keys):
            if k == "intake_results":
                v_str = json.dumps(final_state[k])
            else:
                v_str = json.dumps(final_state[k], indent=4)
                v_str = v_str.replace("\n", "\n    ")
            f.write(f'    "{k}": {v_str}')
            if i < len(keys) - 1:
                f.write(",\n")
            else:
                f.write("\n")
        f.write("}")
        
    logger.info(f"Final state successfully saved to {final_state_path}")

    # Save combined report to a .log file in the logs directory
    master_log_path = os.path.join(logs_dir, "master_report.log")
    with open(master_log_path, "w", encoding="utf-8") as f:
        f.write("="*50 + "\n")
        f.write("ORCHESTRATION COMPLETE - MASTER LOG\n")
        f.write("="*50 + "\n\n")
        if final_state.get("extract_report"):
            f.write("=== EXTRACT REPORT (A2) ===\n")
            f.write(final_state["extract_report"] + "\n\n")
        if final_state.get("requirements_report"):
            f.write("=== REQUIREMENTS REPORT (A3) ===\n")
            f.write(final_state["requirements_report"] + "\n\n")
        if final_state.get("compliance_report"):
            f.write("=== COMPLIANCE REPORT (A4) ===\n")
            f.write(final_state["compliance_report"] + "\n\n")
        if final_state.get("solution_report"):
            f.write("=== SOLUTION ARCHITECTURE REPORT (A5) ===\n")
            f.write(final_state["solution_report"] + "\n\n")
    logger.info(f"Master report saved to {master_log_path}")

    if final_state.get("ppt_structure"):
        ppt_json_path = os.path.join(output_folder, "ppt_structure.json")
        with open(ppt_json_path, "w", encoding="utf-8") as f:
            json.dump(final_state["ppt_structure"], f, indent=2)
        logger.info(f"PPT structure saved to {ppt_json_path}")
        
        try:
            from app import render_pptx
            pptx_output = os.path.join(output_folder, "Architecture_Proposal.pptx")
            render_pptx.render_ppt_from_json(final_state["ppt_structure"], pptx_output)
            logger.info(f"Rendered PPTX saved to {pptx_output}")
            return pptx_output, final_state
        except Exception as e:
            logger.error(f"Failed to render PPTX: {e}")
            return None, final_state
    return None, final_state

# Example Execution
if __name__ == "__main__":
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        base_dir = os.getcwd()  # Fallback for Jupyter Notebooks
        
    output_dir = os.path.join(base_dir, OUTPUT_FOLDER)
    input_dir = os.path.join(base_dir, INPUT_FOLDER)
    
    run_pipeline(input_dir, output_dir)
