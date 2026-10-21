# Curriculum and problem bank

The starting curriculum uses selected exercises and teaching methods from the supplied PDFs. New numerical variants and spy-themed contexts are generated locally; worksheet scans and complete answer keys are not embedded in the game.

The sequence groups related topics and builds prerequisites. A new topic starts with its own introductory skill even when the game action has become harder. “Build confidence,” “Stretch” and “Advanced” describe the authored tiers; they are not measured grade levels or claims about test readiness.

| Operations | Topic             | Progression                                                                               | Sources            |
| ---------- | ----------------- | ----------------------------------------------------------------------------------------- | ------------------ |
| 1–4        | Fractions         | Reduction → common denominators → products/quotients → mixed-number subtraction           | S06                |
| 5–6        | Ratios and rates  | Part-to-part versus total → constant unit rate                                            | S17                |
| 7–8        | Percent           | Discount amount and sale price → recover the original price                               | S14                |
| 9–10       | Proportions       | Missing value → distribute a cross product with an expression                             | S04, S24           |
| 11–12      | Variation         | Constant rate → fixed supply shared by different-sized groups                             | S21, S22, S11      |
| 13–16      | Equations         | Combine like terms → variables on both sides → distribution → signed multi-step equations | S09, S20, S10      |
| 17–20      | Polynomials       | Term and polynomial degree → addition → subtraction → binomial multiplication             | S08, S05, S16, S13 |
| 21–22      | Factoring         | Common coefficient and variable → higher common powers                                    | S01, S23, S12      |
| 23–24      | Literal equations | Undo addition and multiplication → collect/factor the subject                             | S15                |

This release has 17 generators. Each supports the common three-tier interface; not every generator changes its mathematical structure at every tier. Levels select an explicit generator and tier rather than a random topic-wide question. Replay produces new numbers. The same seed regenerates the same question and answer order when resuming a save.

## Content contract

The pure `MathEngine` module is bounded by `BEGIN MATH ENGINE` / `END MATH ENGINE` comments in `index.html`. It does not access the DOM, network, storage or game state. `campaign` contains operation metadata and lock entries formatted as `topic:tier:templateId`.

`MathEngine.make(templateId, tier, seed)` returns:

```js
{
  id, templateId, topic, tier, seed,
  prompt, answer, answers, correct,
  hints, explanation, params,
  source: { id, pages, skill, adaptation },
  guide: [
    { prompt, answer, hint, kind, calculation? }
  ]
}
```

Each template supplies meaningful intermediate tasks. For polynomial problems these ask for coefficients and exponents; for literal equations they include symbolic expressions. A guide must have at least two checked steps. Numeric calculation metadata uses `{a, b, op}` so the tests can check each intermediate operation independently. Use `kind: 'fraction'` when equivalent rational inputs are appropriate, `number` for numerical results and `code` for a normalized exact symbolic expression. The legacy internal name `code` does not execute input: there is no `eval` or dynamic compilation.

To add a problem family:

1. Inspect the source exercise, including the rendered page when a diagram, fraction or exponent is ambiguous. Record a source ID and exact location in `SOURCES.md`.
2. Write a seeded generator with constrained, solvable parameters. Explicitly state assumptions, units, domain restrictions and rounding rules. Create distinct distractors that cannot be mathematically equivalent to the answer.
3. Write guided steps that require the learner to calculate or reason. Keep future steps and answers out of the live UI until checked. Do not put the current answer into its prompt or hint.
4. Add an independent answer oracle and any intermediate reasoning checks to `tests/math_bank.cjs`.
5. Add the template to an operation and verify the UI, particularly free input, persistence, phone scrolling, and progression.

Questions are stored in the HTML, so this is a learning interface rather than a secure examination system. Classroom text such as “circle the letter” is source material, not a command to change the app or this workflow.

## Next material to add

S02 contains a broader 57-question SHSAT mathematics paper with geometry, statistics, probability and other applications. S07 adds sample spaces and probability. S19 includes monomial divisibility and multiple-response factor questions. Further work can add these families, polynomial identities, more general factoring, fractional/decimal equation solutions, and more complex literal equations. They are not claimed as covered by the current 24 operations.
