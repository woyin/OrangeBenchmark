#[no_mangle]
pub extern "C" fn add(a: f64, b: f64) -> f64 {
    a + b
}

#[no_mangle]
pub extern "C" fn sub(a: f64, b: f64) -> f64 {
    a - b
}

#[no_mangle]
pub extern "C" fn mul(a: f64, b: f64) -> f64 {
    a * b
}

#[no_mangle]
pub extern "C" fn div(a: f64, b: f64) -> f64 {
    a / b
}

pub fn eval_expression(expr: &str) -> f64 {
    let mut parser = Parser::new(expr);
    match parser.parse_expression() {
        Some(value) if parser.is_finished() => value,
        _ => f64::NAN,
    }
}

struct Parser<'a> {
    chars: Vec<char>,
    pos: usize,
    _expr: &'a str,
}

impl<'a> Parser<'a> {
    fn new(expr: &'a str) -> Self {
        Self {
            chars: expr.chars().collect(),
            pos: 0,
            _expr: expr,
        }
    }

    fn parse_expression(&mut self) -> Option<f64> {
        let mut value = self.parse_term()?;
        loop {
            self.skip_ws();
            if self.consume('+') {
                value += self.parse_term()?;
            } else if self.consume('-') {
                value -= self.parse_term()?;
            } else {
                break;
            }
        }
        Some(value)
    }

    fn parse_term(&mut self) -> Option<f64> {
        let mut value = self.parse_factor()?;
        loop {
            self.skip_ws();
            if self.consume('*') {
                value *= self.parse_factor()?;
            } else if self.consume('/') {
                value /= self.parse_factor()?;
            } else {
                break;
            }
        }
        Some(value)
    }

    fn parse_factor(&mut self) -> Option<f64> {
        self.skip_ws();
        if self.consume('-') {
            return Some(-self.parse_factor()?);
        }
        if self.consume('(') {
            let value = self.parse_expression()?;
            self.skip_ws();
            return self.consume(')').then_some(value);
        }
        self.parse_number()
    }

    fn parse_number(&mut self) -> Option<f64> {
        self.skip_ws();
        let start = self.pos;
        while self.pos < self.chars.len()
            && (self.chars[self.pos].is_ascii_digit() || self.chars[self.pos] == '.')
        {
            self.pos += 1;
        }
        if start == self.pos {
            return None;
        }
        self.chars[start..self.pos]
            .iter()
            .collect::<String>()
            .parse()
            .ok()
    }

    fn consume(&mut self, expected: char) -> bool {
        self.skip_ws();
        if self.pos < self.chars.len() && self.chars[self.pos] == expected {
            self.pos += 1;
            return true;
        }
        false
    }

    fn skip_ws(&mut self) {
        while self.pos < self.chars.len() && self.chars[self.pos].is_whitespace() {
            self.pos += 1;
        }
    }

    fn is_finished(&mut self) -> bool {
        self.skip_ws();
        self.pos == self.chars.len()
    }
}
