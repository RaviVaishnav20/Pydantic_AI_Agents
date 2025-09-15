from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

@dataclass
class MyState:
    number: int

@dataclass
class Increment(BaseNode[MyState]):
    async def run(self, ctx: GraphRunContext) -> Check42:
        ctx.state.number += 1
        return Check42()

@dataclass
class Check42(BaseNode[MyState, None, int]):
    async def run(self, ctx: GraphRunContext) -> Increment | End[int]:
        if ctx.state.number == 42:
            return Increment()
        else:
            return End(ctx.state.number)

never_42_graph = Graph(nodes=(Increment, Check42))



