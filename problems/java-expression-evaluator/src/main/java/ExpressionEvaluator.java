import java.util.*;

public class ExpressionEvaluator {

    private static final Map<String, Double> BUILTINS = Map.of(
        "pi", Math.PI,
        "e", Math.E
    );

    private static final Set<String> FUNCTIONS = Set.of(
        "sin", "cos", "tan", "sqrt", "abs", "log", "exp"
    );

    public double evaluate(String expression) {
        return evaluate(expression, Map.of());
    }

    public double evaluate(String expression, Map<String, Double> variables) {
        if (expression == null || expression.isBlank()) {
            throw new IllegalArgumentException("Expression cannot be null or empty");
        }
        Map<String, Double> vars = new HashMap<>(BUILTINS);
        if (variables != null) {
            vars.putAll(variables);
        }
        List<String> tokens = tokenize(expression.trim());
        int[] pos = {0};
        double result = parseExpression(tokens, pos, vars);
        if (pos[0] < tokens.size()) {
            throw new IllegalArgumentException("Unexpected token: " + tokens.get(pos[0]));
        }
        return result;
    }

    private List<String> tokenize(String expr) {
        List<String> tokens = new ArrayList<>();
        int i = 0;
        while (i < expr.length()) {
            char c = expr.charAt(i);
            if (Character.isWhitespace(c)) {
                i++;
                continue;
            }
            if (Character.isDigit(c) || c == '.') {
                StringBuilder sb = new StringBuilder();
                while (i < expr.length() && (Character.isDigit(expr.charAt(i)) || expr.charAt(i) == '.')) {
                    sb.append(expr.charAt(i));
                    i++;
                }
                tokens.add(sb.toString());
            } else if (Character.isLetter(c)) {
                StringBuilder sb = new StringBuilder();
                while (i < expr.length() && Character.isLetterOrDigit(expr.charAt(i))) {
                    sb.append(expr.charAt(i));
                    i++;
                }
                tokens.add(sb.toString());
            } else if ("+-*/^()".indexOf(c) >= 0) {
                tokens.add(String.valueOf(c));
                i++;
            } else {
                throw new IllegalArgumentException("Unexpected character: " + c);
            }
        }
        return tokens;
    }

    // Expression: handles addition and subtraction (lowest precedence)
    private double parseExpression(List<String> tokens, int[] pos, Map<String, Double> vars) {
        double left = parseTerm(tokens, pos, vars);
        while (pos[0] < tokens.size()) {
            String op = tokens.get(pos[0]);
            if ("+".equals(op) || "-".equals(op)) {
                pos[0]++;
                double right = parseTerm(tokens, pos, vars);
                if ("+".equals(op)) left += right;
                else left -= right;
            } else {
                break;
            }
        }
        return left;
    }

    // Term: handles multiplication and division
    private double parseTerm(List<String> tokens, int[] pos, Map<String, Double> vars) {
        double left = parsePower(tokens, pos, vars);
        while (pos[0] < tokens.size()) {
            String op = tokens.get(pos[0]);
            if ("*".equals(op) || "/".equals(op)) {
                pos[0]++;
                double right = parsePower(tokens, pos, vars);
                if ("*".equals(op)) left *= right;
                else {
                    if (right == 0) throw new ArithmeticException("Division by zero");
                    left /= right;
                }
            } else {
                break;
            }
        }
        return left;
    }

    // Power: right-associative
    private double parsePower(List<String> tokens, int[] pos, Map<String, Double> vars) {
        double base = parseUnary(tokens, pos, vars);
        if (pos[0] < tokens.size() && "^".equals(tokens.get(pos[0]))) {
            pos[0]++;
            double exponent = parsePower(tokens, pos, vars); // right-associative recursion
            return Math.pow(base, exponent);
        }
        return base;
    }

    // Unary: handles unary minus
    private double parseUnary(List<String> tokens, int[] pos, Map<String, Double> vars) {
        if (pos[0] < tokens.size() && "-".equals(tokens.get(pos[0]))) {
            // Check if this is unary: at start, after operator, or after '('
            pos[0]++;
            double val = parseUnary(tokens, pos, vars);
            return -val;
        }
        if (pos[0] < tokens.size() && "+".equals(tokens.get(pos[0]))) {
            pos[0]++;
            return parseUnary(tokens, pos, vars);
        }
        return parsePrimary(tokens, pos, vars);
    }

    // Primary: numbers, variables, function calls, parenthesized expressions
    private double parsePrimary(List<String> tokens, int[] pos, Map<String, Double> vars) {
        if (pos[0] >= tokens.size()) {
            throw new IllegalArgumentException("Unexpected end of expression");
        }
        String token = tokens.get(pos[0]);

        if ("(".equals(token)) {
            pos[0]++;
            double result = parseExpression(tokens, pos, vars);
            if (pos[0] >= tokens.size() || !")".equals(tokens.get(pos[0]))) {
                throw new IllegalArgumentException("Missing closing parenthesis");
            }
            pos[0]++;
            return result;
        }

        // Try number
        try {
            double num = Double.parseDouble(token);
            pos[0]++;
            return num;
        } catch (NumberFormatException ignored) {}

        // Try function
        if (FUNCTIONS.contains(token)) {
            String func = token;
            pos[0]++;
            if (pos[0] >= tokens.size() || !"(".equals(tokens.get(pos[0]))) {
                throw new IllegalArgumentException("Expected '(' after function " + func);
            }
            pos[0]++;
            double arg = parseExpression(tokens, pos, vars);
            if (pos[0] >= tokens.size() || !")".equals(tokens.get(pos[0]))) {
                throw new IllegalArgumentException("Missing closing parenthesis for function " + func);
            }
            pos[0]++;
            return applyFunction(func, arg);
        }

        // Try variable
        if (vars.containsKey(token)) {
            pos[0]++;
            return vars.get(token);
        }

        // Check if it looks like a variable name but is undefined
        if (token.matches("[a-zA-Z_][a-zA-Z0-9_]*")) {
            throw new IllegalArgumentException("Undefined variable: " + token);
        }

        throw new IllegalArgumentException("Unexpected token: " + token);
    }

    private double applyFunction(String func, double arg) {
        return switch (func) {
            case "sin" -> Math.sin(arg);
            case "cos" -> Math.cos(arg);
            case "tan" -> Math.tan(arg);
            case "sqrt" -> Math.sqrt(arg);
            case "abs" -> Math.abs(arg);
            case "log" -> Math.log(arg);
            case "exp" -> Math.exp(arg);
            default -> throw new IllegalArgumentException("Unknown function: " + func);
        };
    }
}
