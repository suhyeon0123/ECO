import io.shiftleft.codepropertygraph.Cpg
import io.shiftleft.semanticcpg.language._

// Simplify object definition to resolve compatibility issues
def detectSlowVector(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Local] = {
  // cpg.local: Get all local variable nodes
  cpg.local
    // Select local variables where typeFullName matches "vector<.*>"
    .typeFullName("vector<.*>")
    .filter { localVar =>
      // Find identifiers matching localVar.name,
      // Filter for cases where any of the specified method calls exist in inCall,
      // Check if the result is empty
      cpg.identifier
        .name(localVar.name)
        .filter(ident => ident.inCall.name("insert|erase|emplace|emplace_back|assign|clear|swap").nonEmpty)
        .isEmpty
    }
    .l  // Materialize results as List
}



def detectSlowNonHash(cpg: Cpg): List[io.shiftleft.codepropertygraph.generated.nodes.Local] = {
  // cpg.local: Get all local variable nodes
  cpg.local
    // Select local variables where typeFullName matches "(map|set)<.*>"
    .typeFullName("(map|set)<.*>")
    .filter { localVar =>
      // Find identifiers matching localVar.name,
      // Filter for cases where any of the specified method calls exist in inCall,
      // Check if the result is empty
      cpg.identifier
        .name(localVar.name)
        .filter(ident => ident.inCall.name("lower_bound|upper_bound|equal_range|begin|end").nonEmpty)
        .isEmpty
    }
    .l  // Materialize results as List
}