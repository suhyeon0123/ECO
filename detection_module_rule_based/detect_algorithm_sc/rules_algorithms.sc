import io.shiftleft.codepropertygraph.Cpg
import io.shiftleft.semanticcpg.language._
import io.shiftleft.codepropertygraph.generated.nodes.Method
import io.shiftleft.codepropertygraph.generated.nodes.Call
import io.shiftleft.codepropertygraph.generated
import sourcecode.Text.generate






// Function to detect recursive methods that are not related to memoization
def detectSlowRecursive(cpg: Cpg): List[Method] = {
  // 1) Methods identified as recursive (self-calling internal functions)
  
  val recursiveMethods = cpg.method
    .filter(m => !m.isExternal && m.name != "<global>")
    .filter(func => func.ast.isCall.name(func.name).nonEmpty)
    .l

  // 2) find the case where the same identifier is read and written (indirect assignment) in each method
  // can not user faltMap in scala
  val methodsWithCommonIdentifiers = recursiveMethods.map { method =>

    
    // (a) indirect index access: only read
    val methodAccessed = method.ast.isCall.name("<operator>.indirectIndexAccess")
      .filter(call => !call.astParent.assignment.exists(assign => assign.argument(1) == call))
      .map(_.argument(1).code)
      .toSet

    

    // (b) indirect index access: only write
    val methodAssigned = method.ast.isCall.name("<operator>.indirectIndexAccess")
      .where(_.astParent.isCall.name("<operator>.assignment"))
      .map(_.argument(1).code)
      .toSet


    // (c) both read and write
    val commonIdentifiers = methodAccessed.intersect(methodAssigned)

    (method, method.astChildren.l)

    if(commonIdentifiers.nonEmpty) 
      commonIdentifiers.map(id => (method, id))
    else 
      Set.empty[(Method, String)]
      // None
  }.l
  // .flatten
  // .flatten

  // // 2) find the case where the same identifier is read and written (indirect assignment) in each method
  // val methodsWithCommonIdentifiers = recursiveMethods.flatMap { method =>
  //   // (a) indirect index access: only read
  //   val methodAccessed = method.ast.isCall.name("<operator>.indirectIndexAccess")
  //     .filter(call => !call.astParent.assignment.exists(assign => assign.argument(1) == call))
  //     .map(_.argument(1).code)
  //     .toSet


  //   // (b) indirect index access: only write
  //   val methodAssigned = method.ast.isCall.name("<operator>.indirectIndexAccess")
  //     .where(_.astParent.isCall.name("<operator>.assignment"))
  //     .map(_.argument(1).code)
  //     .toSet

  //   // (c) both read and write
  //   val commonIdentifiers = methodAccessed.intersect(methodAssigned)

  //   if(commonIdentifiers.nonEmpty) {
  //     commonIdentifiers.map(id => (method, id))
  //   } else {
  //     Set.empty[(Method, String)]
  //   }
  // }

  // // 2) find the case where the same identifier is read and written (indirect assignment) in each method
  // val methodsWithCommonIdentifiers = recursiveMethods.map { method =>
  //   var ttmp = method.isCall.l

  //   // // (a) indirect index access: only read
  //   // val methodAccessed = method.ast.isCall.name("<operator>.indirectIndexAccess")
  //   //   .filter(call => !call.astParent.assignment.exists(assign => assign.argument(1) == call))
  //   //   .map(_.argument(1).code)
  //   //   .toSet
      

  //   // // (b) indirect index access: only write
  //   // val methodAssigned = method.ast.isCall.name("<operator>.indirectIndexAccess")
  //   //   .where(_.astParent.isCall.name("<operator>.assignment"))
  //   //   .map(_.argument(1).code)
  //   //   .toSet

  //   // // (c) both read and write
  //   // val commonIdentifiers = methodAccessed.intersect(methodAssigned)


  //   if(ttmp.nonEmpty) {
  //     commonIdentifiers.map(id => (method, id))
  //   } else {
  //     Set.empty[(Method, String)]
  //   }
  // }

  // 3) memoizationMethods: the local variable corresponding to the identifier is not declared in the method
  val memoizationMethods = methodsWithCommonIdentifiers.flatten.filter { case (method, identifier) =>
    method.local.name(identifier).isEmpty
  }

  // // 3) memoizationMethods: the local variable corresponding to the identifier is not declared in the method
  // val memoizationMethods = methodsWithCommonIdentifiers.filter { pair =>

  //   var x = pair._1
  //   var y = pair._2

  //   x.local.name(y).isEmpty
  //   // method.local
  //   // pair._1.local.name(pair._2).isEmpty
  // }

  

  // // 3) memoizationMethods: the local variable corresponding to the identifier is not declared in the method
  // val memoizationMethods = methodsWithCommonIdentifiers.filter { 
  //   pair =>
    
  //   if(pair.nonEmpty) {
  //     method.local
  //   }
  //   else{
      
  //   }
  //   method, identifier =>
  //   method.local
  //   // method.local.name(identifier).isEmpty
  // }

  // // 3) memoizationMethods: the local variable corresponding to the identifier is not declared in the method
  // val memoizationMethods = methodsWithCommonIdentifiers.filter { 
  //   pair =>
    
  //   if(pair.nonEmpty) {
  //     method.local
  //   }
  //   else{
      
  //   }
  //   method, identifier =>
  //   method.local
  //   // method.local.name(identifier).isEmpty
  // }
  
  // cpg.method
  //   .filter(m => !m.isExternal && m.name != "<global>")
  //   .filter(func => func.ast.isCall.name(func.name).nonEmpty)
  //   .l

  // 4) final result: the list of recursive methods that are not related to memoization
  val finalResult = recursiveMethods.diff(memoizationMethods.map(_._1)).l
  finalResult
}



def detectSlowBitManipulation(cpg: Cpg): List[Call] = {
  detectMul2(cpg) ++ detectMod2(cpg) ++ detectDiv2(cpg) ++ detectBitFlip(cpg)
}



def detectMul2(cpg: Cpg): List[Call] = {
  cpg.call
    .name("<operator>.multiplication")
    .where(_.argument.order(2).code("2"))
    .l
}


// Further correct optimization
// def detectMul2(cpg: Cpg): List[Call] = {
//   val isTwo = _.isLiteral.where(_.evaluation == 2)
//   cpg.call
//     .name("<operator>.multiplication")
//     .where(_.argument(1).fold(isTwo, isTwo))   // order 1 or 2
//     .l
// }


/**
 * Function to detect modulo 2 operations (% 2).
 * (x % 2) can be changed to (x & 1), and bitwise operations
 */
def detectMod2(cpg: Cpg): List[Call] = {
  cpg.call
    .name("<operator>.modulo")
    .where(_.argument.order(2).code("2"))
    .l
}

def detectDiv2(cpg: Cpg): List[Call] = {
  cpg.call
    .name("<operator>.division")
    .where(_.argument.order(2).code("2"))
    .l
}

/**
 * Function to detect slow bit flip operations using logical negation (e.g., "u[y][x] = !u[y][x]") in the CPG.
 * This function finds call nodes named "<operator>.not" and
 * filters cases where these nodes are used as the right operand in assignment statements.
 */
def detectBitFlip(cpg: Cpg): List[Call] = {
  cpg.call
    .name("<operator>.logicalNot")
    .where(_.astParent.isCall.name("<operator>.assignment"))
    .l
}

// further correct optimization
// def detectBitFlip(cpg: Cpg): List[Call] = {
//   cpg.call
//     .name("<operator>.logicalNot")
//     .where(_.argument(1).evaluationType.is("bool"))  // bool限定
//     .where(_.astParent.isCall.name("<operator>.assignment"))
//     .l
// }