
from scripts.query_parse import QueryParser
from scripts.schema_validation import SchemaValidator
from scripts.sql_generation import SQLGenerator


class QueryPipeline:
    """Parse, validate, and generate safe SQL for a real-estate query."""

    def __init__(self, allowed_cities=None, table_name="listings"):
        self.parser = QueryParser()
        self.validator = SchemaValidator(
            allowed_cities=allowed_cities
        )
        self.sql_generator = SQLGenerator(
            table_name=table_name
        )

    def process(self, query):
        """Return parsed filters and safe SQL, or validation errors."""
        filters = self.parser.parse(query)

        is_valid, errors = self.validator.validate(filters)

        if not is_valid:
            return {
                "success": False,
                "filters": filters,
                "errors": errors,
                "sql": None,
                "params": None,
            }

        sql, params = self.sql_generator.to_sql(filters)

        return {
            "success": True,
            "filters": filters,
            "errors": [],
            "sql": sql,
            "params": params,
        }
