import io.shiftleft.codepropertygraph.Cpg
import io.shiftleft.semanticcpg.language._


def detectSortInLoop(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name("sort|stable_sort")
    .where(_.inAst.isControlStructure.controlStructureType("(FOR|DO|WHILE)"))
    .l
}

def detectfindInLoop(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name("find|find|count_if")
    .where(_.inAst.isControlStructure.controlStructureType("(FOR|DO|WHILE)"))
    .l
}

def detectStringAdd(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name("<operator>.addition")
    .where(_.argument(1).evalType("std::string|std.string"))
    .where(_.inAst.isControlStructure.controlStructureType("(FOR|DO|WHILE)"))
    .where(_.inAssignment)
    .l
}


def detectStringConcat(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name("append|push_back")
    .where(_.argument(0).evalType("std::string|std.string"))
    .where(_.inAst.isControlStructure.controlStructureType("(FOR|DO|WHILE)"))
    .l
}