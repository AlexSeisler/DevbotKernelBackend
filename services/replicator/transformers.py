import libcst as cst

class DocstringUpdateTransformer(cst.CSTTransformer):
    """
    Replaces the first docstring in every top-level function with a new string.
    """
    def __init__(self, new_docstring: str):
        self.new_docstring = new_docstring

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        if not isinstance(updated_node.body, cst.IndentedBlock):
            return updated_node

        if not updated_node.body.body:
            return updated_node

        first_stmt = updated_node.body.body[0]
        if isinstance(first_stmt, cst.SimpleStatementLine) and first_stmt.body and isinstance(first_stmt.body[0], cst.Expr):
            expr = first_stmt.body[0]
            if isinstance(expr.value, cst.SimpleString):
                # Replace the docstring
                new_doc = cst.SimpleStatementLine([
                    cst.Expr(cst.SimpleString(f'"""{self.new_docstring}"""'))
                ])
                new_body = [new_doc] + updated_node.body.body[1:]
                return updated_node.with_changes(body=cst.IndentedBlock(body=new_body))
        return updated_node
