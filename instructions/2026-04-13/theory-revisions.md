# Theory Revision Plan

Date: 2026-04-13
Time: 10:28 JST
Target: `docs/tex/report.tex`
Status: Planning document for theory consolidation before any code changes

## Goal

Consolidate and strengthen the theoretical document before touching the implementation.
The revised theory should become a clean specification for later code audit and future code changes.

This plan follows the intended writing style of the document:
1. start from the most general formulation with the weakest assumptions,
2. state assumptions explicitly when narrowing the model,
3. move to a practical parametric form that is analytically manageable,
4. finish with a worked example / study case.

## High-Level Outcome We Want

At the end of the revision, `docs/tex/report.tex` should:
- define all variables, units, and normalization conventions clearly,
- contain equations that are mathematically consistent and implementable,
- separate general theory from chosen parametric simplifications,
- explain why each simplification is made,
- include a complete study case with reproducible figures,
- be strong enough to serve as the reference for a later code audit.

## Main Issue Clusters To Fix

### 1. Mathematical correctness
- Fix malformed equations and notation, especially the influence kernel and derived effective area.
- Remove mathematically meaningless factors such as `1/e^0`.
- Ensure each displayed equation has a clear interpretation and consistent notation.

### 2. Missing definitions and normalization
- Define units for all important quantities: population, density, area, time, price, cost, probability-like functions.
- Decide and state the normalization of the temporal patterns.
- Clarify whether temporal modulations are probability densities, rates, or dimensionless multiplicative factors.

### 3. Conceptual consistency
- Separate clearly:
  - reservoir size,
  - expected customer flow,
  - per-customer purchase behavior,
  - revenue aggregation,
  - expense aggregation.
- Avoid switching silently between static and time-dependent quantities.

### 4. Probability and menu formulation
- Replace ambiguous conditional probability notation.
- Clarify whether customers buy exactly one item, at least one item, or a basket of items.
- Make the revenue formula consistent with that choice.

### 5. Incomplete temporal modeling
- Complete the missing daily / weekly / yearly construction.
- Introduce the daily pattern explicitly in the final flow equation.
- Explain why separability is assumed and when it is only approximate.

### 6. Study case incompleteness
- Replace the placeholder study case with a full worked example.
- Regenerate or document figures with reproducible scripts and parameters.

### 7. Editorial and structural issues
- Fix typos, captions, grammar, and notation drift. Known specific typo: "stastical" → "statistical" in the document title.
- Add a notation table and a compact assumptions summary.
- Replace `eqnarray` with `align` / `aligned` from `amsmath`.
- Fix the TeX-level exponent bug in the Gaussian kernel: `R_{\mathrm{eff}^2}` must become `R_{\mathrm{eff}}^2` (the exponent is currently inside the `\mathrm{}` group, which silently misrenders).
- Clean the preamble: `\usepackage{eqnarray,...}` is invalid — `eqnarray` is a native LaTeX environment, not a package; remove it from the `\usepackage` line when migrating to `align`.

## Recommended Rewrite Strategy

The revision should not be a line-by-line patch only. It should be a controlled rewrite with this structure:

1. stabilize notation and units first,
2. repair the population reservoir theory,
3. define the time patterns and their normalization,
4. rewrite the menu probability / expected revenue section,
5. rewrite the expenses section with clean units and periods,
6. build a complete study case,
7. regenerate figures from code,
8. only after that compare theory against the Python implementation.

## Proposed Revised Document Structure

### Frontmatter
Add:
- corrected title,
- a short abstract,
- a one-paragraph scope and limitations note.

### Section 1 - Introduction
Keep the current motivation, but tighten it.
Add a short overview of the modeling philosophy:
- explicit assumptions,
- parametric model first,
- empirical calibration later,
- machine learning only as a later enhancement, not as the foundation.

### Section 2 - Theory
Reorganize this section into a more explicit ladder from general to practical:

#### 2.1 Objects, variables, and units
Introduce a notation table early.
This should define, at minimum:
- `N_tot(t)`
- `N_living`, `N_working(t)`, `N_transit(t)`
- `N_c(t)` — **must be declared explicitly as a rate [persons/time] or a count [persons]**. The current text says "number of customers at any given time" (a count) but then integrates it directly to yield revenue (which requires a rate). The notation table must resolve this: if `N_c(t)` is a rate, units are persons/hour; if it is a count, the revenue integral must be re-derived accordingly. This choice propagates into every downstream formula.
- `A`
- `rho`
- `I(r)`
- `R_eff`, `S_eff`
- daily / weekly / yearly modulation functions
- `p(L)`, `c(L)`
- menu-choice probability notation
- `R(Delta t)`, `E_tot(Delta t)`, profit / income

#### 2.2 General population reservoir
State the most general decomposition first:
- total accessible population,
- heterogeneous population groups,
- possible time dependence for each group.

Then explain that the practical model will use a simpler decomposition.

#### 2.3 Practical population reservoir model
This is where the current `N_living`, `N_working`, `N_transit` formulas belong.
For each term:
- define the physical meaning,
- define units,
- explain what is modeled directly and what is absorbed into parameters.

#### 2.4 Spatial influence model
Present the most general influence function first:
- anisotropic, terrain-dependent, route-dependent `I(r,theta)`.

Then introduce the practical simplification:
- isotropic radial kernel `I(r)`.

Then introduce the concrete example kernel:
- Gaussian kernel.

This section should explicitly say:
- whether `I(r)` is normalized to integrate to 1,
- or whether it is only normalized so that `I(0)=1`.

Do not mix these two concepts.

#### 2.5 Daily, weekly, and yearly modulations
This section must replace the current TODO block completely.
It should be written in three levels:

1. Most general statement
- demand depends on multiple timescales and exogenous factors.

2. Practical separable form
- introduce something like `D(t)`, `W(t)`, `Y(t)` or an equivalent time decomposition.
- state that separability is an approximation.

3. Example parametric form
- daily: meal peaks with Gaussian or similar kernels,
- weekly: weekday / weekend scaling,
- yearly: seasonal harmonic or seasonal envelope.

Each of these needs a normalization convention.

### Section 3 - Menu as a source of sales
This section should be rewritten around the correct probabilistic object.

Recommended progression:
1. Most general formulation:
   - purchasing behavior is a time-dependent random process over menu items or baskets.
2. Practical formulation:
   - each customer has a time-dependent probability of choosing items / services.
3. Example formulation:
   - menu-item probabilities or expected basket composition by service period.

Avoid claiming that the current formula is Bayes' rule unless Bayes is actually used.

A cleaner practical target is:
- define a per-customer expected spend at time `t`,
- then multiply by expected customer flow.

## Section-by-Section Fix Plan

### A. Population reservoir and attractiveness

#### Issues to fix
- `N_tot` vs `N_tot(t)` is not handled consistently.
- `A` is described as a probability, but its time basis is not defined.
- the competition formula needs explicit assumptions and indexing. Specifically, the current text defines `n_r` but is ambiguous about whether it counts all restaurants (including self) or only competitors. The formula `A ≈ 1/(n_r+1)` implies `n_r` counts only competitors, but this must be stated explicitly.

#### Required rewrite
- define `A` in the general theory as a product of interpretable factors, ideally treated as approximately orthogonal in the baseline model.
- show how that factorized form reduces to a single effective attractiveness or conversion factor in pedagogical or asymptotic cases.
- explain what happens when there are competitors.
- make the equal-restaurants approximation clearly labeled as a conservative simplification, not a general law.

#### Deliverable in the revised text
- one general factorized formula for `A`,
- one practical simplification,
- one reduced single-factor interpretation for examples or first implementation.

### B. Influence kernel and effective area

#### Issues to fix
- malformed Gaussian notation,
- meaningless `1/e^0`,
- ambiguity between peak normalization and integral normalization,
- inconsistent notation for `R_eff` and `S_eff`.

#### Required rewrite
- write the general spatial influence idea first,
- then choose the Gaussian kernel explicitly as the baseline parametric form,
- note that this aligns with the current code path in `sources/functions_population.py`,
- show the derivation of `S_eff` step by step,
- explain how `rho * S_eff` becomes a count of people,
- keep exponential and hard-cutoff kernels as comparison extensions with a short pro/con discussion.

#### Deliverable in the revised text
- one clean definition of `I(r)` or `I(r,theta)`,
- one clean derivation of `N_living`,
- one explicit statement that the Gaussian kernel is the baseline choice,
- one note on alternative kernels and why they are not used in the baseline model.

### C. Working population and double counting

#### Issues to fix
- `N_{w,i}` and `N^0_{w,i}` are plausible but underdefined.
- double counting between living and working populations is only described informally.

#### Required rewrite
- define clearly what is removed from the working pool,
- explain the de-duplication logic as a set-overlap correction,
- make explicit that this is a practical approximation.

#### Deliverable in the revised text
- a clean interpretation of the working term,
- one small worked example with two work sites.

### D. Transit population

#### Issues to fix
- `N_transit = 0` is presented as if it were general.

#### Required rewrite
- move this to the study-case assumptions or practical simplifications.
- keep transit as a legitimate model term in the general theory.

#### Deliverable in the revised text
- transit remains in the general model,
- the chosen study case may set it to zero explicitly.

### E. Daily / weekly / yearly demand patterns

#### Issues to fix
- the daily pattern is discussed but missing from the final equation.
- the weekly / yearly patterns are not fully defined.
- normalization is unspecified.

#### Required rewrite
- choose a notation that clearly separates the three timescales.
- write the final practical form with all intended components.
- adopt integral normalization as the preferred theory reference.
- explain why this is the preferred theoretical form, and then list alternative normalization conventions with short pros/cons for implementation.

#### Deliverable in the revised text
- one general decomposition,
- one practical separable formula,
- one example parameterization,
- one short comparison table of normalization choices.

#### Locked decision on cascaded normalization
The baseline choice is **integral normalization** for each modulator over its own period. However, when `D(t)`, `W(t)`, and `Y(t)` are all integral-normalized over their respective periods, their pointwise product is not itself a rate or a dimensionless number without further convention. The comparison table must address this explicitly. Recommended baseline resolution: only `D(t)` carries the rate interpretation [persons/hour]; `W(t)` and `Y(t)` are dimensionless multiplicative envelopes normalized so that their mean over their own period equals 1. The table should then list peak-normalization as an alternative and provide a short pro/con for each.

### F. Menu probability model

#### Issues to fix
- `P(t|L)` is conceptually reversed for the intended use.
- the normalization condition over items and time is unclear.
- the current text mixes at-least-one-item language with item-level probabilities without a basket model.
- the constraint `sum_L integral P(t|L) dt >= 1` is presented as a normalization condition, but it is not: it is a lower bound on a quantity that is not a probability density and whose units have not been defined. Before any constraint or bound is written, the correct probabilistic object must be defined and its proper normalization stated. The rewrite must not preserve this inequality in any form until the object it applies to is well-defined.

#### Required rewrite
- choose whether the basic object is:
  - `P(L|t)`,
  - expected basket composition at time `t`,
  - or service-level expected spend.
- keep multi-item purchases in the general baseline theory.
- define a reduced special case for single effective spend or single-item behavior when needed for pedagogy or first implementation.
- define the relationship between menu-item probabilities and expected revenue per customer.

#### Deliverable in the revised text
- one precise probabilistic definition,
- one explicit normalization statement,
- one general multi-item baseline,
- one practical approximation used later by the code.

### G. Expected revenue

#### Issues to fix
- revenue inherits the menu-notation ambiguity,
- the current formula is hard to read and hides assumptions.
- the current revenue formula uses `\propto` (proportional to) and the text explicitly discards the normalization constant. This must not be carried forward: a practical revenue model must be a proper equality. The proportionality must be replaced by `=` and the normalization must be derived explicitly from the customer-flow definition and the menu-probability normalization established in section F.

#### Required rewrite
- derive revenue in layered form:
  1. expected customer flow,
  2. expected spend per customer,
  3. aggregated revenue over time.
- add the discrete-time approximation used for numerical implementation.

#### Deliverable in the revised text
- one clean continuous-time formula,
- one clean discrete-time approximation,
- one short interpretation paragraph.

### H. Expenses and profit

#### Issues to fix
- the text lists four expense groups but the final equation does not include all of them coherently.
- payment fees are only partly formalized.
- recurring/staff periodicity is not fully explained.

#### Required rewrite
- define each expense family explicitly,
- include fixed / one-time costs in the most general expense model,
- derive a reduced operating model when one-off costs are intentionally set aside,
- define the expected payment-fee model cleanly,
- define operating profit / income explicitly.

#### Deliverable in the revised text
- one clean expense decomposition,
- one clean profit equation,
- one brief note distinguishing operating profit from startup / one-off costs.

### I. Study case

#### Issues to fix
- placeholder text only,
- figures exist but are not fully documented or reproducible.

#### Required rewrite
- start with a pedagogical worked example with a full parameter table,
- then extend to a richer and more realistic case while staying analytically understandable,
- explain which assumptions are chosen for each stage of the study case,
- tie each plot to a formula and a parameter choice,
- interpret the result qualitatively,
- keep `N_transit = 0` as a clean limit case and optionally show a small-transit variant such as 5 percent if it stays readable.

#### Deliverable in the revised text
- a pedagogical study case followed by a richer extension,
- a reproducible figure-generation workflow,
- consistent captions and filenames.

## Figures and Plot Plan

The revised theory should include both conceptual figures and numerical plots.
These help because the document progresses from general formulation to practical form.

### Conceptual figures

#### 1. Population reservoir schematic
Purpose:
- show residents, work sites, restaurant position, and effective reach.

Possible output:
- simple SVG-based conceptual figure exported to PNG.

Suggested location:
- `docs/tex/graphics/fig_population_schematic.png`

#### 2. Influence kernel comparison
Purpose:
- compare Gaussian, exponential, and hard-cutoff kernels.
- explain why the chosen baseline is retained.

Suggested location:
- `docs/tex/graphics/fig_kernel_comparison.png`

#### 3. Time-scale decomposition schematic
Purpose:
- show the logic of daily, weekly, and yearly modulation.
- emphasize general form vs practical separable approximation.

Suggested location:
- `docs/tex/graphics/fig_timescale_decomposition.png`

#### 4. Revenue construction schematic
Purpose:
- show the flow from population reservoir to customer flow to per-customer spend to total revenue.

Suggested location:
- `docs/tex/graphics/fig_revenue_pipeline.png`

### Numerical plots

#### 5. Daily pattern examples
- meal peaks for breakfast / lunch / dinner.
- compare a generic day and a weekend day.

Suggested location:
- `docs/tex/graphics/fig_daily_patterns.png`

#### 6. Weekly modulation
- normalized weekly pattern over seven days.

Suggested location:
- `docs/tex/graphics/fig_weekly_pattern.png`

#### 7. Yearly modulation
- annual seasonal curve with explicit normalization.

Suggested location:
- `docs/tex/graphics/fig_yearly_pattern.png`

#### 8. Menu-item time profiles or expected service spend
- show time dependence of selected items or services.

Suggested location:
- `docs/tex/graphics/fig_menu_time_profiles.png`

#### 9. Study-case revenue / cost / profit plots
- daily and monthly views.
- these can replace or supersede the current JPGs.

Suggested locations:
- `docs/tex/graphics/Fig_breakfast.png`
- `docs/tex/graphics/Fig_main_afternoon.png`
- `docs/tex/graphics/Fig_Jan.png`
- `docs/tex/graphics/Fig_Year.png`

### Reproducibility plan for plots
- store plot-generation scripts in a dedicated reproducible location rather than burying them in ad hoc notes.
- recommended path for future scripts:
  - `sources/figures/` if they are closely tied to the Python model,
  - or `docs/tex/scripts/` if they are document-only figure builders.
- use Python-generated figures for numerical examples and computed curves.
- use SVG-based diagrams for conceptual or algorithmic schematics, then export them to PNG if needed by the TeX workflow.
- store figure parameters in a small JSON file when practical.
- each figure used in the TeX document should be traceable to a script and parameter set.

## Concrete Writing Rules For The Revision

### Rule 1: always separate three levels
For each major modeling block, use this order:
1. general form,
2. practical simplification,
3. example instantiation.

### Rule 2: assumptions must be explicit
When the text narrows from the general to the practical form, add a short sentence beginning with:
- `We now assume...`, or
- `For the baseline model, we assume...`.

### Rule 3: define normalization immediately
Any introduced modulation or probability-like object must state:
- its domain,
- whether it is dimensionless,
- its normalization rule,
- how it enters aggregated quantities.

### Rule 4: distinguish specification from scenario
The theory must distinguish:
- what belongs to the general model,
- what belongs to the baseline parametric model,
- what belongs only to the study case.

### Rule 5: document practical limitations honestly
For each practical approximation, add one short note about what reality it ignores.
That fits the original spirit of explicit assumptions and model limits.

## Locked Decisions From Author Feedback

These choices are now part of the working specification for the theory rewrite.

1. Meaning of `A`
- In the general theory, `A` should be written as a product of interpretable factors.
- The baseline assumption is approximate orthogonality between these factors, so the product remains compact.
- The text should then show how this reduces to a single effective attractiveness or conversion factor in pedagogical or first-implementation cases.

2. Baseline spatial kernel
- Keep the Gaussian influence kernel as the baseline parametric choice.
- This is aligned with the current code in `sources/functions_population.py`, where `Influence_fct` uses a Gaussian radial decay and `Nliving` uses the matching effective-area formula.
- Alternative kernels should be discussed as extensions or comparisons, not as co-equal baseline models.

3. Preferred temporal normalization
- The preferred theory reference is the integral-based normalization.
- The document should present the integral form first because it is the clearest mathematically.
- The document should also list alternative normalization choices and give a short pro/con discussion relative to the integral form.

4. Purchase model baseline
- The general baseline theory should allow multi-item purchases.
- Reduced single-item or single-effective-spend cases may then be introduced as pedagogical simplifications or implementation shortcuts.

5. Customer-group structure
- The general theory should allow group-specific structures for residents, workers, and transit populations whenever the notation can stay compact.
- The practical baseline may collapse to a shared structure when parameter count would otherwise explode.

6. Transit population in examples
- Keep `N_transit = 0` as an explicit limit case.
- If it stays readable, include an additional example with a small transit contribution such as 5 percent.

7. Fixed / one-time costs
- Include fixed or one-time costs in the most general expense model.
- Then derive a reduced operating-profit view by adding assumptions when those one-time costs are intentionally excluded.

8. Yearly modulation
- Start from a simple yearly modulation in the baseline theory.
- Then discuss holidays, events, and richer exogenous effects as layered extensions.

9. Study-case progression
- Start with a pedagogical example first.
- Then increase complexity and realism while staying analytically understandable.
- This also supports later property-style or unit-style tests derived from the theory.

10. Figure strategy
- Use Python-generated figures for graphs based on real computed values or worked examples.
- Use SVG-style diagrams for general conceptual views or algorithmic schematics.

## Remaining Non-Blocking Writing Choices

No blocking modeling questions remain at this stage.
The remaining choices are editorial or notation-level and can be settled during the actual rewrite, for example:
- the exact symbolic factorization of `A`,
- whether customer groups are indexed by a generic symbol such as `g` or written out explicitly in the main text,
- whether the normalization comparison belongs in the main text or an appendix.

## Suggested Order Of Execution

### Phase 1 - Formalize locked conventions
- write the chosen factorized form of `A`,
- fix units and domains,
- adopt the Gaussian kernel as the baseline spatial form,
- adopt integral normalization as the preferred theory reference for temporal patterns,
- state the multi-item purchase baseline and the reduced special cases.

### Phase 2 - Rewrite the theory core
- rewrite population reservoir,
- rewrite influence model,
- rewrite temporal modulations,
- rewrite menu probability formulation,
- rewrite revenue and expense equations.

### Phase 3 - Build the study case
- define example parameters,
- generate figures,
- write captions and interpretation,
- add limitations discussion.

### Phase 4 - Prepare for code audit
- extract a compact mathematical specification,
- list which equations the code is expected to implement,
- then move to the theory-vs-code comparison.

## Immediate Next Step

The main modeling decisions are now resolved.
The next step is to turn this plan into a tightened mathematical specification and then rewrite `docs/tex/report.tex` accordingly.
Once that is done, the theory-vs-code audit will have a stable target.
