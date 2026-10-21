# Curriculum and problem bank

The curriculum uses selected exercises and teaching methods from the supplied PDFs. New numerical variants and spy-themed contexts are generated locally; worksheet scans and complete answer keys are not embedded in the game.

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

This release has 38 generators (17 original, 15 added for Shadow Atlas objectives, and 6 for vehicle engineering). Each supports the common three-tier interface; not every generator changes its mathematical structure at every tier. Levels select an explicit generator and tier rather than a random topic-wide question. Replay produces new numbers. The same seed regenerates the same question and answer order when resuming a save.

## Shadow Atlas: applications and advanced extensions

Operations 25–36 revisit the topic groups in order, adding applications before advanced algebra. Difficulty is grouped by prerequisite, not guaranteed to increase after every individual question. The first 24 operation definitions and their seeded questions are unchanged, preserving existing saves. All 36 operations can be selected from the lobby.

| Operation | Adventure / location                      | New maths                                                                              | Sources                            |
| --------- | ----------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------- |
| 25        | Whiteout Cipher / Arctic relay            | Mixed-number division; interpreting fractional lengths                                 | S06, pp. 29–31                     |
| 26        | Aurora Blackout / polar bunker            | Unit conversion before simplifying a ratio                                             | S11, pp. 3–4                       |
| 27        | Mask of the Magpie / Venice               | Linked ratios with a shared middle quantity                                            | S17, p. 4, problem 7               |
| 28        | The Glass Auction / Venice                | Fractional percents; comparing a part to a base                                        | S14, pp. 6, 10–13                  |
| 29        | Sun Dial / desert observatory             | Similar shadows and proportional scale                                                 | S24, pp. 3–4, example 6            |
| 30        | Mirage Exchange / desert outpost          | Currency exchange as direct variation; exact cents                                     | S21, p. 1, problem 5               |
| 31        | Jade Vector / jungle archive              | Identify every valid monomial factor among candidates                                  | S19, p. 1, part A                  |
| 32        | Temple of Factors / jungle temple         | Count all monomial factors; greatest common factors with several variables             | S19, pp. 1–2; S01 and S23, p. 1    |
| 33        | Abyss Signal / underwater station         | Inverse variation in gears and fixed-distance travel                                   | S11, pp. 7–8; S22, p. 1, problem 5 |
| 34        | The Silent Current / underwater lab       | Factor a subject out of a multivariable literal equation                               | S15, p. 2, problem 27              |
| 35        | Caldera Protocol / volcanic fortress      | Variable denominators, cross multiplication and excluded values                        | S24, pp. 2 and 5                   |
| 36        | Zero Hour Atlas / volcanic command center | Two-solution proportions via a quadratic; cumulative factoring/literal-equation review | S24, p. 3, example 5; S01, S15     |

The last two operations explicitly handle denominator restrictions. The final family generates factorable quadratics with two valid real roots and checks both. Factor-list guides require each candidate to be classified, while factor-count guides enumerate coefficient divisors and count allowable exponents before multiplying. These are adaptations of the worksheet skills, with new numbers and spy contexts.

## Vehicle engineering

Car and motorcycle escapes each have two maths checkpoints, reached at one-third and two-thirds of the route. Traffic and health are frozen until the task is completed. Correct results earn a temporary boost and protection. The learner operates a mixing valve or chooses a road by steering; these tasks use the same seeded generator and checked-guide contract as the cases.

| Operation range | Motorcycle: dispatch junction                       | Car: fuel lab                               | Sources                                          |
| --------------- | --------------------------------------------------- | ------------------------------------------- | ------------------------------------------------ |
| 1–6             | Fraction of a route, then add the starting marker   | Allocate fuel using a fraction of the total | S06, pp. 21–22                                   |
| 7–16            | Percentage of a route, then add the starting marker | Allocate fuel using a percentage            | S14, pp. 6–7                                     |
| 17–36           | Closing speed, meeting time and meeting position    | Divide a total in a part-to-part ratio      | S09, pp. 1–2; S21, p. 1, problem 1; S17, pp. 1–2 |

These are newly authored applications of the listed methods, not copied vehicle questions from the worksheets. Moving-courier problems specify constant speeds, a common start time and a common direction. Fuel allocations use integer litres; percent products are stored exactly to avoid displaying floating-point artifacts. Every unfinished vehicle guide resumes at the validated prefix of checked answers. Completing a guide reveals its solution but still requires the learner to operate the valve or select the exit.

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

Each template supplies meaningful intermediate tasks. For polynomial problems these ask for coefficients and exponents; for literal equations they include symbolic expressions. A guide must have at least two checked steps. Numeric calculation metadata uses `{a, b, op}` so the tests can check each intermediate operation independently. Use `kind: 'set'` for comma-separated numerical sets (order does not matter, duplicates are rejected), and `kind: 'text'` for a short word or variable. Use `kind: 'fraction'` when equivalent rational inputs are appropriate, `number` for numerical results and `code` for a normalized exact symbolic expression. The legacy internal name `code` does not execute input: there is no `eval` or dynamic compilation.

To add a problem family:

1. Inspect the source exercise, including the rendered page when a diagram, fraction or exponent is ambiguous. Record a source ID and exact location in `SOURCES.md`.
2. Write a seeded generator with constrained, solvable parameters. Explicitly state assumptions, units, domain restrictions and rounding rules. Create distinct distractors that cannot be mathematically equivalent to the answer.
3. Write guided steps that require the learner to calculate or reason. Keep future steps and answers out of the live UI until checked. Do not put the current answer into its prompt or hint.
4. Add an independent answer oracle and any intermediate reasoning checks to `tests/math_bank.cjs`.
5. Add the template to an operation and verify the UI, particularly free input, persistence, phone scrolling, and progression.

Questions are stored in the HTML, so this is a learning interface rather than a secure examination system. Classroom text such as “circle the letter” is source material, not a command to change the app or this workflow.

## Next material to add

S02 contains a broader 57-question SHSAT mathematics paper with geometry, statistics, probability and other applications. S07 adds sample spaces and probability. Further work can add these families, polynomial identities, general non-factorable quadratics, fractional/decimal linear-equation solutions, and further literal-equation structures. They are not claimed as covered by the current 36 operations.
