import io.shiftleft.codepropertygraph.Cpg
import io.shiftleft.semanticcpg.language._


// def detectSlowIO(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
//   detectCinCout(cpg) ++ detectStringStream(cpg) ++ detectGetcharInLoop(cpg)
// }

def detectCinCout(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Identifier] = {
  cpg.identifier
    .name("cin|cout")
    .l
}

def detectStringStream(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Local] = {
  cpg.local
    .typeFullName("stringstream")
    .l
}

def detectGetcharInLoop(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name("getchar|fgetc")
    .where(x => x.inAst.isControlStructure.controlStructureType("(FOR|DO|WHILE)"))
    .l
} 







// def detectSlowMathLibrary(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
//   detectPowArg1(cpg) ++ detectPowArg2(cpg) ++ detectPowInt(cpg) ++ detectLiteralMath(cpg) ++ detectLoopInvariantMathCalls(cpg)
// }


/**
 * Function to detect pow(2, n) operations.
 * These operations can be replaced with bitwise operations.
 * pow(2, n) can be changed to (1 << n), and bitwise operations
 * are faster than pow operations, which can improve performance.
 */
def detectPowArg1(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name("pow")
    .where(_.argument(1).code("2|4|8|16"))
    .l
}


def detectPowArg2(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name("pow")
    .where(_.argument(2).code("2|3"))
    .l
}


def detectPowInt(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name("pow")
    .where(_.argument.order(1).isLiteral)
    .where(_.argument.order(2).isLiteral)
    .l
}

val mathFunctions_arg1 = List("sqrt", "exp", "log", "log10", "sin", "cos", "tan", "asin", "acos", "atan")

def detectLiteralMath(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name(mathFunctions_arg1*)
    .where(_.argument(1).evalType("double|float|int"))
    .l
}


def detectLoopInvariantMathCalls(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Call] = {
  cpg.call
    .name(mathFunctions_arg1*)
    .where(_.inAst.isControlStructure.controlStructureType("(FOR|DO|WHILE)"))
    .where(_.argument(1).isIdentifier)
    .filter { callNode =>

      val identifierName = callNode.argument(1).code
      val LoopInvariant = callNode.inAst.isControlStructure.controlStructureType("(FOR|DO|WHILE)")
      val incIdentifiers = LoopInvariant.ast
        .filterNot(_.isBlock)
        .assignment
        .target
        .isIdentifier
        .map(_.name)
        .toSet
      !incIdentifiers.contains(identifierName)
    } 
    .l  
}

