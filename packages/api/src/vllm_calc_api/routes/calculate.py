"""The calculation endpoint — thin wrapper over the engine (no logic here)."""

from fastapi import APIRouter

from vllm_calc_engine.calculate import calculate as engine_calculate
from vllm_calc_engine.models import CalcInput, CalcResult

router = APIRouter(tags=["calculate"])


@router.post("/calculate", response_model=CalcResult)
def calculate(inp: CalcInput) -> CalcResult:
    # Engine domain errors (e.g. InvalidParallelism) propagate to the registered
    # exception handlers, which render the structured error contract.
    return engine_calculate(inp)
