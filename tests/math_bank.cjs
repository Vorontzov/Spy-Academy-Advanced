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
function oracle(q) {
  const p = q.params;
  switch (q.templateId) {
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
assert.equal(e.campaign.length, 36);
for (const s of e.campaign) {
  assert.equal(s.count, s.locks.length);
  assert(s.floors >= 8 && s.floors <= 24);
  for (const lock of s.locks) {
    const [topic, tier, template] = lock.split(":");
    const q = e.make(template, Number(tier), "campaign");
    assert.equal(q.topic, topic);
    assert(q.source);
  }
}
console.log(
  `PASS: ${count} independent answers, ${steps} checked guided inputs, all source references and 36 maths-first missions.`,
);
