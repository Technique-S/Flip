"""Additive local-reference project contract; frozen v1 projects stay unchanged."""

from typing import Literal, Self

from pydantic import Field, model_validator

from flip_core.models import (
    Candidate,
    Chain,
    ComparisonPlan,
    Contract,
    Limits,
    Name,
    Source,
)


class LocalComparisonPlan(ComparisonPlan):
    referenceAlias: None = None


class LocalProject(Contract):
    schemaVersion: Literal["m3-1.0.0"]
    projectId: Name
    chainId: Chain
    toolVersion: Literal["0.1.0"]
    sources: list[Source] = Field(min_length=1, max_length=1251)
    candidate: Candidate
    referenceCandidate: Candidate
    comparison: LocalComparisonPlan
    limits: Limits

    @model_validator(mode="after")
    def explicit_interfaces(self) -> Self:
        sources = {s.alias: s for s in self.sources}
        if len(sources) != len(self.sources):
            raise ValueError("duplicate source alias")
        for design in (self.candidate, self.referenceCandidate):
            widths = {}

            def check(pin, design=design, widths=widths):
                width = design.nIn if pin.component is None else widths.get(pin.component)
                if width is None or pin.pin >= width:
                    raise ValueError("out-of-range or forward/cyclic pin mapping")

            for component in design.components:
                if component.instanceId in widths:
                    raise ValueError("duplicate component identity")
                for pin in component.inputs:
                    check(pin)
                if component.kind == "REF":
                    source = sources.get(component.sourceAlias)
                    if source is None or source.nState or len(component.inputs) != source.nIn:
                        raise ValueError("missing source, stateful source, or incorrect arity")
                    if int(source.identity.circuitId) >= 2**64:
                        raise ValueError("REF ID exceeds uint64")
                    widths[component.instanceId] = source.nOut
                else:
                    widths[component.instanceId] = 1
            for pin in design.outputs:
                check(pin)
        a, b = self.referenceCandidate, self.candidate
        if a.nIn != b.nIn or len(a.outputs) != len(b.outputs):
            raise ValueError("incompatible actual design interfaces")
        if sorted(self.comparison.inputMap) != list(range(a.nIn)):
            raise ValueError("complete input bijection required")
        if sorted(self.comparison.outputMap) != list(range(len(a.outputs))):
            raise ValueError("complete output bijection required")
        return self
