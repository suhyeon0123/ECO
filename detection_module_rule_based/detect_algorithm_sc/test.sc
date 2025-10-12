import io.shiftleft.codepropertygraph.Cpg
import replpp.Operators._
import replpp.Colors
import java.io.{File, PrintWriter, FileWriter}
import java.nio.file.{Files, Paths}

import upickle.default._

implicit val colors: Colors = Colors.BlackWhite

import io.shiftleft.codepropertygraph.generated.nodes.StoredNode
import java.nio.file.{Files, Paths}
import java.nio.charset.StandardCharsets
import scala.jdk.CollectionConverters._
import scala.util.Using



def escapeJsonString(s: String): String = {
  s.flatMap {
    case '"' => "\\\""
    case '\\' => "\\\\"
    case '\b' => "\\b"
    case '\f' => "\\f"
    case '\n' => "\\n"
    case '\r' => "\\r"
    case '\t' => "\\t"
    case c if c.isControl => "\\u%04x".format(c.toInt)
    case c => c.toString
  }
}

def saveAsJson(results: List[StoredNode], outputPath: String): Unit = {
  val mappedResults = results.map { node =>
    val nodeType = escapeJsonString(node.label())
    val properties = node.propertiesMap.asScala.toMap.map { case (k, v) =>
      val key = escapeJsonString(k)
      val value = escapeJsonString(v.toString)
      s""""$key": "$value""""
    }.mkString(", ")

    s"""{
       |  "type": "$nodeType",
       |  "elements": { $properties }
       |}""".stripMargin
  }

  val json =
    s"""{
       |  "results": [
       |    ${mappedResults.mkString(",\n    ")}
       |  ]
       |}""".stripMargin

  val path = Paths.get(outputPath)
  Files.write(path, json.getBytes(StandardCharsets.UTF_8))
}


@main def main(cpgPath: String, outputPath: String) = {
  
    val cpgOpt = importCpg(cpgPath)
    

    val outputDir = new File(outputPath)
    if (!outputDir.exists()) {
      outputDir.mkdirs()
    }

    val detectionResults = Map(
      "slow_recursive" -> detectSlowRecursive(cpg),
      "mul2" -> detectMul2(cpg),
      "mod2" -> detectMod2(cpg),
      "div2" -> detectDiv2(cpg),
      "bit_flip" -> detectBitFlip(cpg),
      
      "slow_vectors" -> detectSlowVector(cpg),
      "slow_non_hash" -> detectSlowNonHash(cpg),
      
      "cin_cout" -> detectCinCout(cpg),
      "string_stream" -> detectStringStream(cpg),
      "getchar_in_loop" -> detectGetcharInLoop(cpg),
      "pow_arg1" -> detectPowArg1(cpg),
      "pow_arg2" -> detectPowArg2(cpg),
      "pow_int" -> detectPowInt(cpg),
      "literal_math" -> detectLiteralMath(cpg),
      "loop_invariant_math" -> detectLoopInvariantMathCalls(cpg),
      
      "sort_in_loop" -> detectSortInLoop(cpg),
      "find_in_loop" -> detectfindInLoop(cpg),
      "string_add" -> detectStringAdd(cpg),
      "string_concat" -> detectStringConcat(cpg)
    )
    

    for ((name, results) <- detectionResults if results.nonEmpty) {
      saveAsJson(results, s"$outputPath/$name.json")
    }
    

    val summaryCategories = Map(
      "Algorithm" -> List(
        ("Slow Recursive Functions", "slow_recursive"),
        ("Multiply by 2 Operations", "mul2"),
        ("Modulo by 2 Operations", "mod2"),
        ("Division by 2 Operations", "div2"),
        ("Bit Flip Operations", "bit_flip")
      ),
      "Data Structures" -> List(
        ("Inefficient Vector Usage", "slow_vectors"),
        ("Inefficient Non-Hash Container Usage", "slow_non_hash")
      ),
      "Library Usage" -> List(
        ("cin/cout Usage", "cin_cout"),
        ("String Stream Usage", "string_stream"),
        ("getchar in Loop", "getchar_in_loop"),
        ("pow(2, n) Usage", "pow_arg1"),
        ("pow(x, 2|3) Usage", "pow_arg2"),
        ("Integer pow Usage", "pow_int"),
        ("Literal Math Function Calls", "literal_math"),
        ("Loop Invariant Math Calls", "loop_invariant_math")
      ),
      "Others" -> List(
        ("Sort in Loop", "sort_in_loop"),
        ("find in Loop", "find_in_loop"),
        ("String Addition Operations", "string_add"),
        ("String Concatenation Operations", "string_concat")
      )
    )
    
    val summaryBuilder = new StringBuilder("===== Detection Results Summary =====\n\n")
    
    for ((category, items) <- summaryCategories) {
      summaryBuilder.append(s"== $category ==\n")
      for ((label, key) <- items) {
        summaryBuilder.append(s"$label: ${detectionResults(key).size}\n")
      }
      summaryBuilder.append("\n")
    }
    
    val summary = summaryBuilder.toString
    
    val summaryPath = s"$outputPath/summary.txt"
    Files.write(Paths.get(summaryPath), summary.getBytes)
    
    println(s"Analysis results saved to: $outputPath")
}
