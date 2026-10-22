const assert = require("node:assert/strict"),
  fs = require("node:fs"),
  vm = require("node:vm");
const html = fs.readFileSync(
  require("node:path").join(__dirname, "../index.html"),
  "utf8",
);
const ctx = vm.createContext({});
vm.runInContext(
  html.match(/\/\/ BEGIN MATH ENGINE[\s\S]*?\/\/ END MATH ENGINE/)[0] +
    "\nthis.engine=MathEngine",
  ctx,
);
const e = ctx.engine;
const gcd = (a, b) => (b ? gcd(b, a % b) : Math.abs(a));
const frac = (a, b) => {
  let k = gcd(a, b);
  return b / k === 1 ? String(a / k) : `${a / k}/${b / k}`;
};
const poly = (a, b, c) =>
  [
    [a, "x²"],
    [b, "x"],
    [c, ""],
  ]
    .filter(([n]) => n !== 0)
    .map(
      ([n, v], i) =>
        (i ? (n < 0 ? " − " : " + ") : n < 0 ? "−" : "") +
        (v && Math.abs(n) === 1 ? "" : Math.abs(n)) +
        v,
    )
    .join("") || "0";
const rational = (s) => {
  const [a, b = "1"] = String(s).split("/");
  return Number(a) / Number(b);
};
const compare = (a, op, b) =>
  op === "<" ? a < b : op === ">" ? a > b : op === "≤" ? a <= b : a >= b;
function regionContains(answer, x) {
  if (answer === "all real numbers") return true;
  if (answer === "no real solution") return false;
  if (answer.startsWith("all real numbers except "))
    return x !== Number(answer.slice(24));
  if (answer.startsWith("x = ")) return x === Number(answer.slice(4));
  return answer.split(" or ").some((part) => {
    let m = part.match(/^x ([<>≤≥]) (-?\d+)$/);
    if (m) return compare(x, m[1], Number(m[2]));
    m = part.match(/^(-?\d+) ([<≤]) x ([<≤]) (-?\d+)$/);
    if (m)
      return compare(Number(m[1]), m[2], x) && compare(x, m[3], Number(m[4]));
    throw Error("Unparsed interval " + answer);
  });
}
function checkRegion(q, predicate, bounds) {
  const probes = Array.from({ length: 161 }, (_, i) => i * 2 - 160).concat(
    bounds.flatMap((x) => [x - 0.25, x, x + 0.25]),
  );
  for (const x of probes)
    assert.equal(regionContains(q.answer, x), predicate(x), q.id + " at " + x);
  for (const wrong of q.answers.filter((s) => s !== q.answer))
    assert(
      probes.some((x) => regionContains(wrong, x) !== predicate(x)),
      q.id + " equivalent distractor " + wrong,
    );
}

function oracle(q) {
  const p = q.params;
  switch (q.templateId) {
    case "compass-triangle":
      return p.mode === 2 ? p.total / 3 : 3 * p.side * p.scale;
    case "triangle-range": {
      if (p.mode === 3) {
        let n = 0;
        for (let x = 1; x < p.a + p.b; x++)
          if (x + p.a > p.b && x + p.b > p.a) n++;
        return String(n);
      }
      checkRegion(
        q,
        (x) => x > 0 && x + p.a > p.b && x + p.b > p.a && p.a + p.b > x,
        [p.b - p.a, p.a + p.b],
      );
      return q.answer;
    }
    case "triangle-order": {
      const vertices = p.labels
        .map((label, i) => ({ label, angle: p.angles[i] }))
        .sort((a, b) => a.angle - b.angle);
      assert.equal(
        p.angles.reduce((x, y) => x + y, 0),
        180,
      );
      return vertices
        .map((v) =>
          p.labels
            .filter((x) => x !== v.label)
            .sort()
            .join(""),
        )
        .join(", ");
    }
    case "inequality-two-step":
      checkRegion(q, (x) => compare(p.a * x + p.b, p.op, p.c), [p.bound]);
      return q.answer;
    case "inequality-distribute":
    case "inequality-both-sides":
      checkRegion(
        q,
        (x) => compare(p.a * (p.b * x + p.c) + p.d, p.op, p.e * x + p.rhs),
        [p.bound],
      );
      return q.answer;
    case "absolute-inside":
    case "absolute-outside":
      checkRegion(
        q,
        (x) =>
          compare(
            Math.abs(x + p.shift),
            p.inside ? (p.inclusive ? "≤" : "<") : p.inclusive ? "≥" : ">",
            p.radius,
          ),
        [-p.radius - p.shift, p.radius - p.shift],
      );
      return q.answer;
    case "system-classify": {
      const augmented = p.a * p.rhs - p.k * p.a * p.c;
      assert.equal(p.a * (p.k * p.b) - p.b * (p.k * p.a), 0);
      return augmented === 0 ? "infinitely many solutions" : "no solution";
    }
    case "square-root-property": {
      const root = Math.sqrt((p.rhs - p.b) / p.a);
      assert(Number.isFinite(root));
      const actual = q.answer
        .split(" and ")
        .map(rational)
        .sort((a, b) => a - b);
      assert.equal(actual.length, root === 0 ? 1 : 2);
      actual.forEach((x) => assert(Math.abs(p.a * x * x + p.b - p.rhs) < 1e-8));
      return root === 0 ? "0" : `${frac(-p.n, p.d)} and ${frac(p.n, p.d)}`;
    }
    case "zero-product-linear":
      return `${frac(-p.b, p.a)} and ${frac(p.d, p.c)}`;
    case "quadratic-nonmonic": {
      const roots = q.answer.split(" and ").map(rational);
      assert.equal(roots.length, 2);
      roots.forEach((x) =>
        assert(Math.abs(p.A * x * x + p.B * x + p.C) < 1e-8),
      );
      const split = q.guide[1].answer.split(",").map(Number);
      assert.equal(split[0] + split[1], p.B);
      assert.equal(split[0] * split[1], p.A * p.C);
      return `${frac(-p.b, p.a)} and ${frac(-p.d, p.c)}`;
    }
    case "quadratic-repeated":
      assert.equal(p.B * p.B - 4 * p.A * p.C, 0);
      assert(Math.abs(rational(q.answer) + p.B / (2 * p.A)) < 1e-10);
      return q.answer;
    case "quadratic-formula": {
      const D = p.B * p.B - 4 * p.A * p.C;
      assert(D > 0);
      for (const sign of [-1, 1]) {
        const x = p.center + sign * Math.sqrt(p.rad);
        assert(Math.abs(p.A * x * x + p.B * x + p.C) < 1e-8);
      }
      let square = 1;
      for (let i = 1; i * i <= D; i++) if (D % (i * i) === 0) square = i * i;
      assert.equal(Number(q.guide[5].answer), square);
      return `${-p.B / (2 * p.A)} ± sqrt(${D / (4 * p.A * p.A)})`;
    }
    case "discriminant-count": {
      // Evaluate the vertex relative to zero instead of reusing the discriminant.
      const x = -p.B / (2 * p.A),
        minimum = p.A * x * x + p.B * x + p.C;
      return minimum < 0 ? 2 : minimum === 0 ? 1 : 0;
    }
    case "quadratic-interval":
    case "quadratic-normalize":
      checkRegion(q, (x) => compare(p.A * x * x + p.B * x + p.C, p.op, 0), [
        p.lo,
        p.hi,
      ]);
      return q.answer;
    case "quadratic-double-root":
      checkRegion(q, (x) => compare(p.A * (x - p.root) ** 2, p.op, 0), [
        p.root,
      ]);
      return q.answer;

    case "mixed-to-improper":
      return frac(p.whole * p.d + p.n, p.d);
    case "improper-to-mixed":
      return `${Math.floor(p.N / p.d)} ${frac(p.N % p.d, p.d)}`;
    case "fraction-expression":
      return frac((p.a * p.d + p.c * p.b) * p.e, p.b * p.d * p.f);
    case "percent-decimal":
      return (p.p * p.whole) / 100;
    case "percent-missing-whole":
      return (p.part * 100) / p.p;
    case "successive-discounts":
      return (p.price * (100 - p.p) * (100 - p.s)) / 10000;
    case "sales-tax-cents": {
      const tax = Number((BigInt(p.cents) * BigInt(p.tax) + 50n) / 100n);
      assert.equal(Number(q.guide[2].answer), tax);
      return (p.cents + tax) / 100;
    }
    case "discount-then-tax": {
      const cut = Number((BigInt(p.cents) * BigInt(p.discount) + 50n) / 100n);
      const reduced = p.cents - cut,
        tax = Number((BigInt(reduced) * BigInt(p.tax) + 50n) / 100n);
      assert.equal(Number(q.guide[1].answer), cut);
      assert.equal(Number(q.guide[3].answer), tax);
      return (reduced + tax) / 100;
    }
    case "commission-threshold":
      return p.base + ((p.sales - p.quota) * p.p) / 100 + p.bonus;
    case "profit-base":
      return p.onSale
        ? (p.saleCents * (100 - p.p)) / 10000
        : p.saleCents / (100 + p.p);
    case "tiered-tax": {
      let tax = 0;
      for (let dollar = 0; dollar < p.income; dollar++)
        tax += dollar < p.first ? p.a : dollar < p.first + p.next ? p.b : p.c;
      return tax / 100;
    }
    case "mean-readings":
      return p.values.reduce((a, b) => a + b, 0) / p.values.length;
    case "missing-mean":
      return p.mean * 4 - p.known.reduce((a, b) => a + b, 0);
    case "weighted-mean":
      return frac(p.n * p.a + p.m * p.b, p.n + p.m);
    case "round-trip-speed":
      return frac(2 * p.a * p.b, p.a + p.b);
    case "signed-route":
      return p.a + p.b - p.c - p.d;
    case "power-order": {
      assert.equal(
        Number(q.guide[2].answer),
        p.inside ? p.a ** 2 : -(p.a ** 2),
      );
      return (
        (p.inside ? p.a ** 2 : -(p.a ** 2)) + (p.b * p.d) / p.c - p.e + p.f
      );
    }
    case "balanced-distribution": {
      const roots = [];
      for (let x = -100; x <= 100; x++)
        if (p.A * (p.B * x + p.C) === p.D * (p.E * x + p.F)) roots.push(x);
      assert.equal(roots.length, 1);
      return roots[0];
    }
    case "fraction-linear":
      return frac(p.rhs * p.b * p.d + p.a * p.d - p.c * p.b, p.b + p.d);
    case "literal-denominator": {
      // Substitute several independent u,k values into the rearranged expression.
      for (const k of [1, 2, 4])
        for (const u of [1, 3, 5]) {
          const a = -p.n / (k * u + p.p);
          assert(Math.abs((-p.p * a - p.n) / (k * a) - u) < 1e-9);
        }
      return `-${p.n}/(k*u+${p.p})`;
    }
    case "system-eliminate": {
      const x = frac(p.R * p.c + p.b * p.S, p.a * (p.b + p.c)),
        y = frac(p.R - p.S, p.b + p.c);
      assert.equal(q.guide[2].answer, y);
      assert.equal(q.guide[5].answer, x);
      return `(${x}, ${y})`;
    }
    case "system-scale": {
      const determinant = p.a * p.d + p.b * p.c,
        x = frac(p.R * p.d + p.b * p.S, determinant),
        y = frac(p.c * p.R - p.a * p.S, determinant);
      assert.equal(q.guide[8].answer, x);
      assert.equal(q.guide[11].answer, y);
      assert.equal(
        Number(q.guide[0].answer) * p.b,
        Number(q.guide[3].answer) * p.d,
      );
      return `(${x}, ${y})`;
    }
    case "quadratic-factors": {
      if (p.kind === "zero") return `0 and ${frac(p.b, p.a)}`;
      if (p.kind === "squares")
        return `${frac(-p.b, p.a)} and ${frac(p.b, p.a)}`;
      const roots = [];
      for (let x = -30; x <= 30; x++)
        if (x * x + p.B * x + p.C === 0) roots.push(x);
      assert.equal(roots.length, 2);
      const factors = q.guide[0].answer.split(",").map(Number);
      assert.equal(factors[0] + factors[1], p.B);
      assert.equal(factors[0] * factors[1], p.C);
      // Distractors must not be equivalent to the correct unordered root set.
      for (const value of q.answers.filter((v) => v !== q.answer)) {
        const pair = value
          .split(" and ")
          .map(Number)
          .sort((a, b) => a - b);
        assert.notEqual(JSON.stringify(pair), JSON.stringify(roots));
      }
      return roots.join(" and ");
    }
    case "radical-verification": {
      const roots = [];
      for (let x = -100; x <= 100; x++)
        if (
          p.a * x + p.b >= 0 &&
          Math.abs(Math.sqrt(p.a * x + p.b) - p.c) < 1e-12
        )
          roots.push(x);
      if (p.c < 0) {
        assert.equal(roots.length, 0);
        assert.equal(q.guide.at(-1).answer, "no");
        return "no real solution";
      }
      assert.equal(roots.length, 1);
      assert.equal(q.guide.at(-1).answer, "yes");
      return roots[0];
    }

    case "route-fraction":
    case "route-percent":
      return p.start + (p.length * p.num) / p.den;
    case "fuel-fraction":
    case "fuel-percent":
      return (p.total * p.num) / p.den;
    case "fuel-ratio":
      return (p.total * p.a) / (p.a + p.b);
    case "route-intercept": {
      const meetings = [];
      for (let minutes = 1; minutes < 100; minutes++)
        if (p.speed * minutes === p.lead + p.courier * minutes)
          meetings.push(p.speed * minutes);
      assert.equal(meetings.length, 1);
      return meetings[0];
    }
    case "reduce":
      return frac(p.a, p.b);
    case "fraction-sum":
      return frac(p.a * p.d + (p.subtract ? -1 : 1) * p.c * p.b, p.b * p.d);
    case "fraction-product":
      return frac(p.a * (p.divide ? p.d : p.c), p.b * (p.divide ? p.c : p.d));
    case "mixed-fractions":
      return frac((p.w * p.b + p.a) * p.d - (p.v * p.d + p.c) * p.b, p.b * p.d);
    case "share-ratio":
      return (p.total * p.b) / (p.a + p.b);
    case "unit-rate":
      return (p.distance * p.target) / p.minutes;
    case "percent-change":
      return p.reverse ? p.price : p.price * (1 - p.p / 100);
    case "proportion":
      return p.c / p.b - p.offset;
    case "direct-variation":
      return (p.days * p.target) / p.count;
    case "inverse-variation":
      return (p.people * p.days) / p.newPeople;
    case "combine-equation": {
      const candidates = [];
      for (let x = -100; x <= 100; x++)
        if (p.a * x + p.b * x + p.d === p.c * x + p.rhs) candidates.push(x);
      assert.equal(candidates.length, 1);
      return candidates[0];
    }
    case "distribute-equation": {
      const candidates = [];
      for (let x = -100; x <= 100; x++)
        if (p.a * (p.b * x + p.c) + p.d === p.rhs) candidates.push(x);
      assert.equal(candidates.length, 1);
      return candidates[0];
    }
    case "poly-degree":
      return Math.max(p.a + p.b, p.c);
    case "poly-combine":
      return poly(p.a + p.sign * p.d, p.b + p.sign * p.e, p.c + p.sign * p.f);
    case "poly-product":
      return poly(p.a * p.c, p.a * p.d + p.b * p.c, p.b * p.d);
    case "common-factor": {
      assert.equal(gcd(p.k * p.a, p.k * p.b), p.k);
      for (let x = 1; x < 5; x++)
        assert.equal(
          p.k * p.a * x ** (p.p + 1) + p.k * p.b * x ** p.p,
          p.k * x ** p.p * (p.a * x + p.b),
        );
      return `${p.k}x^${p.p}(${p.a}x + ${p.b})`;
    }
    case "literal-equation":
      return p.advanced ? `${p.a}/(y − ${p.b})` : `(y − ${p.b})/${p.a}`;
    case "mixed-quotient":
      assert.equal(
        gcd(p.pieceN, p.pieceD),
        1,
        "Reciprocal guide uses the displayed fraction’s numerator and denominator",
      );
      return frac((p.whole * p.d + p.n) * p.pieceD, p.d * p.pieceN);
    case "unit-ratio":
      return `${(p.minutes * 60) / gcd(p.minutes * 60, p.seconds)}:${p.seconds / gcd(p.minutes * 60, p.seconds)}`;
    case "linked-ratios": {
      const g = gcd(p.a * p.c, p.b * p.d);
      return `${(p.a * p.c) / g}:${(p.b * p.d) / g}`;
    }
    case "fractional-percent":
      return (p.whole * p.percent) / 100;
    case "percent-comparison":
      return (p.part * 100) / p.whole;
    case "shadow-scale":
      return (p.height * p.towerShadow) / p.shadow;
    case "currency-exchange":
      return (p.received * p.newEuros) / p.euros / 100;
    case "monomial-factor-list": {
      const valid = p.candidates
        .map((v, i) =>
          p.coefficient % v.c === 0 && p.a - v.x >= 0 && p.b - v.y >= 0
            ? "ABCD"[i]
            : null,
        )
        .filter(Boolean);
      assert.equal(valid.length, 2);
      for (let i = 0; i < 4; i++)
        assert.equal(
          q.guide[i + 1].answer,
          valid.includes("ABCD"[i]) ? "yes" : "no",
        );
      return valid.join(" and ");
    }
    case "factor-count": {
      let count = 0;
      for (let n = 1; n <= p.n; n++)
        for (let x = 0; x <= p.a; x++)
          for (let y = 0; y <= p.b; y++) if (p.n % n === 0) count++;
      return count;
    }
    case "multivariable-gcf": {
      for (let x = 1; x <= 3; x++)
        for (let y = 1; y <= 3; y++)
          assert.equal(
            p.k * p.a * x ** (p.p + 1) * y ** p.z -
              p.k * p.b * x ** p.p * y ** (p.z + 1),
            p.k * x ** p.p * y ** p.z * (p.a * x - p.b * y),
          );
      assert.equal(gcd(p.k * p.a, p.k * p.b), p.k);
      return `${p.k}x^${p.p}y^${p.z}(${p.a}x − ${p.b}y)`;
    }
    case "gear-train":
      return frac(p.teethB * p.rpmB, p.teethA);
    case "inverse-speed":
      return frac(p.v1 * p.time1, p.v2);
    case "literal-network":
      return `u/(${p.a}*c-${p.b}*d)`;
    case "rational-proportion": {
      const roots = [];
      for (let x = -100; x <= 100; x++)
        if (x !== -p.b && x !== -p.d && p.a * (x + p.d) === p.c * (x + p.b))
          roots.push(x);
      assert.equal(roots.length, 1);
      assert.equal(roots[0], p.x);
      assert.equal(q.guide.at(-1).answer, `${-p.b}, ${-p.d}`);
      return roots[0];
    }
    case "quadratic-proportion": {
      const roots = [];
      for (let x = -100; x <= 100; x++)
        if (x !== p.d && (x + p.a) * (x - p.d) === p.k * p.c) roots.push(x);
      assert.equal(roots.length, 2);
      assert.equal(q.guide.at(-1).answer, roots.join(", "));
      const pair = q.guide.at(-2).answer.split(",").map(Number);
      assert.equal(pair[0] + pair[1], p.a - p.d);
      assert.equal(pair[0] * pair[1], -p.a * p.d - p.k * p.c);
      return `x = ${roots[0]} or x = ${roots[1]}`;
    }
    case "mixed-supply":
      return frac((p.w * p.d + p.n) * p.b, p.d * (p.v * p.b + p.a));
    case "consecutive-code": {
      const first = (p.total - (p.gap * p.count * (p.count - 1)) / 2) / p.count;
      assert.equal(Number(q.guide[3].answer), first);
      return first + (p.count - 1) * p.gap;
    }
    case "coin-count": {
      const solutions = [];
      for (let b = 0; b <= p.count; b++)
        if (p.low * (p.count - b) + p.high * b === p.value) solutions.push(b);
      assert.equal(solutions.length, 1);
      return solutions[0];
    }
    case "ticket-ledger": {
      const solutions = [];
      for (let a = 0; a <= p.count; a++)
        if (p.low * a + p.high * (p.count - a) === p.revenue) solutions.push(a);
      assert.equal(solutions.length, 1);
      return solutions[0];
    }
    case "interest-plan": {
      const I = ((p.principal * p.rate) / 100) * p.years;
      return p.monthly ? (p.principal + I) / (12 * p.years) : I;
    }
    case "interest-unknown":
      return p.time
        ? p.interest / ((p.principal * p.rate) / 100)
        : (100 * p.interest) / (p.principal * p.years);
    case "fraction-rebuild": {
      const solutions = [];
      for (let n = 1; n < 1000; n++)
        if ((n + p.change) * p.v === p.u * (p.k * n + p.b + p.change))
          solutions.push(n);
      assert.equal(solutions.length, 1);
      const n = solutions[0],
        d = p.k * n + p.b;
      assert.equal(Number(q.guide[4].answer), n);
      assert.equal(Number(q.guide[5].answer), d);
      return frac(n, d);
    }
    case "age-offset": {
      const solutions = [];
      for (let y = 1; y < 100; y++)
        if (p.nowRatio * y + p.years === p.laterRatio * (y + p.years))
          solutions.push(y);
      assert.equal(solutions.length, 1);
      assert.equal(Number(q.guide[2].answer), solutions[0]);
      return p.nowRatio * solutions[0] - p.past;
    }
    case "mixture-water": {
      const added = Number(q.answer);
      assert(
        Math.abs(p.volume * p.initial - (p.volume + added) * p.target) < 1e-7,
      );
      return p.volume * (p.initial / p.target - 1);
    }
    case "mixture-blend": {
      const high = Number(q.answer);
      assert(high > 0 && high < p.volume);
      assert(
        Math.abs(
          p.high * high + p.low * (p.volume - high) - p.target * p.volume,
        ) < 1e-7,
      );
      assert.equal(Number(q.guide[0].answer), (p.volume * p.low) / 100);
      assert(
        Math.abs(Number(q.guide[1].answer) - (p.volume * p.target) / 100) <
          1e-8,
      );
      return (p.volume * (p.target - p.low)) / (p.high - p.low);
    }
    case "work-together": {
      const hours = rational(q.answer);
      assert(
        Math.abs(hours / p.a + ((p.drain ? -1 : 1) * hours) / p.b - 1) < 1e-9,
      );
      return frac(p.a * p.b, p.drain ? p.b - p.a : p.a + p.b);
    }
    case "meeting-motion":
      return (60 * p.distance) / (p.a + p.b);
    case "pursuit-motion": {
      const hours = rational(q.answer);
      assert(Math.abs(p.fast * hours - p.slow * (p.head + hours)) < 1e-8);
      return frac(p.slow * p.head, p.fast - p.slow);
    }
    case "river-current":
      return (
        p.distance / (p.still + p.current) + p.distance / (p.still - p.current)
      );
    case "pythagoras-route":
      return Math.sqrt(p.leg ? p.c * p.c - p.a * p.a : p.a * p.a + p.b * p.b);
    case "trapezoid-roof":
      return ((p.a + p.b) * p.h * p.unit) / 2;
    case "tank-volume":
      return frac(
        p.length * p.width * p.height * p.num,
        p.den * (p.pump ? p.rate : 1),
      );
    case "signal-probability": {
      const chips = [
        ...Array(p.blue).fill("b"),
        ...Array(p.gold).fill("g"),
        ...Array(p.red).fill("r"),
      ];
      let favorable = 0,
        total = 0;
      if (p.single) {
        favorable = p.blue;
        total = chips.length;
      } else
        for (let i = 0; i < chips.length; i++)
          for (let j = 0; j < chips.length; j++)
            if (p.replaced || i !== j) {
              total++;
              if (chips[i] === "b" && chips[j] === "g") favorable++;
            }
      return frac(favorable, total);
    }
    default:
      throw Error("Missing oracle " + q.templateId);
  }
}
let count = 0,
  steps = 0;
for (const temp of e.templates)
  for (let t = 1; t <= 3; t++) {
    const variants = new Set();
    for (let seed = 0; seed < 200; seed++) {
      const q = e.make(temp.id, t, seed),
        expected = oracle(q);
      if (typeof expected === "number")
        assert(Math.abs(Number(q.answer) - expected) < 1e-8, q.id);
      else assert.equal(q.answer, expected, q.id);
      assert.equal(q.answers[q.correct], q.answer);
      assert.equal(new Set(q.answers).size, q.answers.length);
      assert(q.answers.length >= 3);
      if (e.templates.indexOf(temp) >= 80) {
        for (const wrong of q.answers.filter((x) => x !== q.answer))
          assert(
            Math.abs(rational(wrong) - rational(q.answer)) > 1e-9,
            q.id + " equivalent choice",
          );
        if (q.templateId === "interest-plan" && t === 3)
          assert(
            Number.isInteger(Number(q.answer)),
            q.id + " payment must be an exact whole-dollar amount",
          );
      }
      assert.equal(JSON.stringify(q), JSON.stringify(e.make(temp.id, t, seed)));
      assert(q.guide.length >= 2);
      assert(q.source?.id && q.source.pages);
      assert(q.hints.length === 2);
      assert(!/undefined|NaN|Infinity/.test(JSON.stringify(q)));
      for (const s of q.guide) {
        assert(e.matchesStep(s, s.answer), q.id + " " + s.prompt);
        assert(!e.matchesStep(s, ""));
        assert(!e.matchesStep(s, "NaN"));
        assert(!e.matchesStep(s, "<script>"));
        if (s.calculation) {
          const { a, b, op } = s.calculation;
          const exp =
            op === "+"
              ? a + b
              : op === "−"
                ? a - b
                : op === "×"
                  ? a * b
                  : a / b;
          assert(
            Math.abs(Number(s.answer) - exp) < 1e-8,
            q.id + " " + s.prompt,
          );
        }
        steps++;
      }
      if (q.templateId === "reduce") {
        assert.equal(Number(q.guide[0].answer), gcd(q.params.a, q.params.b));
      }
      if (q.templateId === "fraction-sum") {
        assert.equal(
          Number(q.guide[0].answer),
          (q.params.b * q.params.d) / gcd(q.params.b, q.params.d),
        );
      }
      variants.add(q.prompt);
      count++;
    }
    assert(variants.size > 10, temp.id + " insufficient variants");
  }
assert(e.matchesStep({ kind: "fraction", answer: "1/2" }, "2/4"));
assert(!e.matchesStep({ kind: "fraction", answer: "1/2" }, "1/0"));
assert(e.matchesStep({ kind: "code", answer: "(y − 3)/2" }, " ( y - 3 ) / 2 "));
assert.equal(e.campaign.length, 96);
for (const s of e.campaign) {
  assert.equal(s.count, s.locks.length);
  assert(s.floors >= 8 && s.floors <= 34);
  for (const lock of [...s.locks, ...(s.interiorLocks || [])]) {
    const [topic, tier, template] = lock.split(":");
    const q = e.make(template, Number(tier), "campaign");
    assert.equal(q.topic, topic);
    assert(q.source);
  }
}
console.log(
  `PASS: ${count} independent answers, ${steps} checked guided inputs, all source references and 96 maths-first missions.`,
);
