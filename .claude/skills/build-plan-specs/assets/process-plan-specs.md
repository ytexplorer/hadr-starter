# The implementation specification planning process

Start from a detailed product description, and systematically turn that into an implementation specifications.

This is achieved through a combination of these agent skills:
`/grill-with-docs` + `/shaping` + `/to-issues`.

If you do not have them yet, install them using:

```shell
npx skills add -g mattpocock/skills --skill grill-with-docs
npx skills add -g rjs/shaping-skills --skill shaping --skill to-issues
```

## Documents

### Exist prior to this session

- REQS.md - Initial idea, created via handwritten capture of thoughts
- QUESTIONS.md - Scratch file primarily used by `/grill-with-docs`
- CONTEXT.md - Contains shared language/terms/definitions, created via `/grill-with-docs`
- docs/adr/*.md - Architectural decision records, created via `/grill-with-docs`
- docs/PRD.md - User stories, problem statement, solution description, implementation decisions, testing decisions, out of scope, created via `/to-prd`
- FRAME.md - Succinct product definition, created via `/shaping`
- SHAPING.md - Requirements, shapes, RxS fit matrix, detailed selected shape, created via `/shaping`
- SPIKE-*.md - Used to ideate and decide on changes to requirements or shapes to achieve better RxS fit
- BREADBOARD.md - Affordances and how they are connected, created via `/shaping`

### Produced during this session

- SLICES.md - Splitting up of breadboard items into horizontal chunks of work, created via `/shaping`
- SLICE-V*.md - Detailed slices, created via `/shaping`
- ARCHITECTURE.md - Technical architecture specification
- TESTING.md - Results of an audit of the test plans for each slice, including suggested fixes
- issues/NNNN-iss-*.md - Detail for an issue ticket for implementation
- issues/NNNN-epic-*.md - Detail for an epic ticket for implementation, that is the parent of 2 or more issue tickets

## Steps

### F - Shaping - Slicing

(F1) Slice - Break the breadboard into vertical implementation increments. Each slice must end in demo-able UI.

> Model hint: Medium, FRESH context
> Prompts:

```text
/shaping
status: process has been completed up to breadboarding
use for context: FRAME.md + CONTEXT.md + docs/PRD.md + docs/adr/*.md
use shaping outputs: SHAPING.md + BREADBOARD.md
task: next step, slice
```

(F2) Slice details - Turn the slice candidates into detailed slice plans, with 1 file per slice.

> Model hint: High, reuse context
> Prompts:

```text
- proceed with next step: create slice details
- file name pattern: SLICE-Vn.md (e.g. SLICE-V1.md)
```

(F3) Add more detailed test plans to slices

> Model hint: High, reuse context
> Prompts:

```text
for each slice file:
- add a "Test Plan" heading, and within it:
- add new "End-to-End Tests" subheading, and move the existing acceptance criteria into that
- add new "Integration Tests" subheading, and add a list of 1-line integration test descriptions
- add new "Unit Tests" subheading, and add a list of 1-line unit test descriptions
- do not describe in detail what each test does, only top level descriptions
```

### G - Grill with docs - Tech architecture

(G1) Generate an architecture file as a first pass.
This is necessary because so far we have been technology agnostic,
but now it is time to commit to a particular "stack", and to specific approaches/techniques.

> Model hint: Medium, FRESH context
> Prompts:

```text
create ARCHITECTURE.md based on CONTEXT.md + docs/PRD.md + BREADBOARD.md + SLICES.md + docs/adr/*.md using the template at https://raw.githubusercontent.com/timajwilliams/architecture/refs/heads/main/architecture.md
```

(G2) Grill about architectural decisions.
The default assumptions made in the first pass may not have been the correct ones.
Prod to ensure that ADRs have been created if needed

> Model hint: Medium, reuse context
> Prompts:

```text
/grill-with-docs
- focus on the new ARCHITECTURE.md
- grill me on this
- add all questions up front and as you go to QUESTIONS.md
```

```text
(…answers to 1 or more questions)

Based on the answers to the questions, ensure that ADRs are created/updated in docs/adr/*.md
Also update CONTEXT.md + docs/PRD.md and any other files if needed.
Then update QUESTIONS.md to reflect where these questions' resolutions can be found.
Also add all new questions you have to QUESTIONS.md (if any)
```

(G3) Prod tech stack questions + prod to ensure that ADRs have been created if needed

> Model hint: Medium, reuse context
> Prompts:

```text
- focus on ARCHITECTURE.md specifically technology choices that have not been made:
  languages/ libraries/ frameworks/ environments/ deployments/ persistence/ APIs/ 3rd party services/ etc
- grill me on this
- add all questions up front and as you go to QUESTIONS.md
```

```text
(…answers to 1 or more questions)

Based on the answers to the questions, ensure that ADRs are created/updated in docs/adr/*.md
Update CONTEXT.md + docs/PRD.md and any other files, if needed.
Then update QUESTIONS.md to reflect where these questions' resolutions can be found.
Also add all new questions you have to QUESTIONS.md (if any)
```

(G4) Separate research queries. Use google search bar directly, and look for LLM response.

> Model hint: N/A (best to use google directly in browser)
> Prompts:

```text
help me to choose (…tech stack module/package/library/framework) for (…desired feature).
suggest 3, and provide the tradeoffs.
context: (…provide relevant context only)
```

examples:

```text
help me to choose an npm package for scheduling an hourly trigger.
suggest 3, and provide the tradeoffs.
context: application server is a single server instance. tasks do not need to persist if server crashes or restarts. simple server that hourly polls 3 different 3rd party data sources and aggregates results.
```

## H - Grill with docs - Testing

(H1) Load context window to prepare for tests audit

> Model hint: Medium, FRESH context
> Prompts:

```text
/grill-with-docs
- read FRAME.md + CONTEXT.md + ARCHITECTURE.md to get up to speed
- on-demand, only if-and-when needed: read any other *.md files (incl subdirs) for further context
- add all questions up front, and as you go, to QUESTIONS.md
- read the "## Test Plan" section in each SLICE-V*.md file
- do not do anything further, simply acknowledge
```

(H2) Audit tests

> Model hint: High, reuse context
> Prompts:

```text
- Are there any missing tests?
- Are there any duplicate/ overlapping tests?
- Should any tests move to a different category? (end-to-end tests, integration tests, unit tests)
- Are any tests not specific to the features implemented within the current slice? (if not, where should they be moved?)
- Do any tests reveal poor planning or poor architecture? (if so, what is the insight?)
- Output your findings to TESTING.md
- Add all questions up front, and as you go, to QUESTIONS.md
```

(H3) Answer questions that arose during the test audit

> Model hint: Medium, reuse context
> Prompts:

```text
(…answers to 1 or more questions)

Based on the answers to the questions, ensure that ADRs are created/updated in docs/adr/*.md
Also update CONTEXT.md + docs/PRD.md and any other files if needed.
Then update QUESTIONS.md to reflect where these questions' resolutions can be found.
Also add all new questions you have to QUESTIONS.md (if any)
Update TESTING.md if needed to reflect answers given or new/updated ADRs.
Do no update SLICE-V*.md files yet
```

(H4) Update test plans within detailed slices

> Model hint: Medium, reuse context
> Prompts:

```text
(…answers to 1 or more questions)

- Based on the findings in TESTING.md update the "## Test Plan" section in each SLICE-V*.md file
- Add all questions up front, and as you go, to QUESTIONS.md
```

## I - To issues - Create epic and individual tickets

(I1) Load up context window to prepare to create tickets

> Model hint: Medium, FRESH context
> Prompts:

```text
- read FRAME.md + CONTEXT.md + ARCHITECTURE.md + SHAPING.md for context
- read BREADBOARD.md + SLICES.md + SLICE-V*.md in detail
- do not do anything further, just acknowledge
```

(I2) Answer any new questions, if any

> Model hint: High, reuse context
> Prompts:

```text
(…answers to 1 or more questions)

- Based on the findings in TESTING.md update the "## Test Plan" section in each SLICE-V*.md file
- Add all questions up front, and as you go, to QUESTIONS.md
```

(I3) From each slice, create 1 epic ticket, and 2 or more issue tickets, as files

> Model hint: High, reuse context
> Prompts:

```text
/to-issues from SLICE-V*.md
- create an *epic* issue whose title begins with "epic"
  - represents all of the issues in a single SLICE-V*.md
  - do NOT detail each issue, instead link to them
  - file name: issues/NNN-epic-vN-*.md where NNN is an incrementing number, and `vN` is the slice ID
- each item under "## Build Plan" in each SLICE-V*.md should result in 1 proto-issue, at first
- subsequently, separate these proto-issues into logical groups based on:
  - what should be worked on at the same time
  - what does not make sense to work on independently vs in parallel
  - group issues only when >= 80% sure they can be combined
  - each group must have >= 2 issues - don't combine all proto-issues into a single issue
- then combine all the proto-issues in each logical group into a single issue
  - file name: issues/NNN-iss-vN-*.md
- do NOT issue any github commits/API calls or `gh` commands, instead create each issue as a MD file in issues/*
- finally update issues/000-prd.md to link to each of the epics
```

(I4) Create minimal manual tests per epic

> Model hint: Medium, reuse context
> Prompts:

```text
- Review each epic: issues/NNN-epic-vN-*.md + its linked issues
- Update `## Acceptance criteria`:
  - Create a `### Happy path test` section
    - Select 1 specific representative scenario, where user accomplishes the intended outcome
    - Write detailed steps for user to perform manually
    - Write assertions for user to verify manually
    - Interleave steps and assertions in order that user should do them
  - Create a `### Failure path manual test` section
    - Select 1 specific representative scenario, where user fails, e.g. gets stuck/errors
    - Write interleaved steps and assertions
- Intent: Augment programmatic E2E tests with manual verification that the user can perform to verify that a core part of the epic has been implemented
```
