import io.shiftleft.codepropertygraph.Cpg
import replpp.Operators._
import replpp.Colors

@main def main(cpgPath: String) = {
    implicit val colors: Colors = Colors.BlackWhite

    importCpg(cpgPath)
}
