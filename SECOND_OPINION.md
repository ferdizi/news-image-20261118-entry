# Second opinion — news-image-20261118 (Gadiel's rule: "jangan mikir sendiri")

Date: 2026-11-18 ~15:10 WIB. Model used for reference/review ONLY —
the poster build stays in this recorded session with Muse Spark.

## What was tried

- Xingchi gpt-6.1-sol (helper
  ~/workspace/custom-connectors/custom.xingchiapi/bin/xingchi_chat.py):
  FAILED. `models` lists gpt-6.1-sol, but /v1/chat/completions returns
  HTTP 403 Forbidden (both with max_tokens 200 and 1500). The key's
  chat access appears dead as of 2026-11-18 ~15:10 WIB — needs a new
  key from Gadiel if Xingchi is to be used again. (100milionseek was
  NOT tried: local key is dead 401 by design; the working key lives
  only on Railway.)
- OpenRouter free model nvidia/nemotron-3-ultra-550b-a55b:free
  (helper ~/workspace/custom-connectors/custom.openrouter/bin/
  openrouter_chat.py): WORKED, $0, 2 calls of the 50/day free limit.
  First call truncated at 1500 max_tokens (finish_reason length);
  second call (corrected prompt, max_tokens 3000) completed
  (finish_reason stop, 837 completion tokens).
  Raw replies: /tmp/ni18-study/second-opinion-openrouter.txt and
  second-opinion-openrouter2.txt. Prompt files: second-opinion-prompt.txt,
  second-opinion-prompt2.txt.

## What the model said (2nd call, complete)

A. Three angles: (1) Africa main — promote Ebola or Guinea from
   also-on; (2) Latin America main — promote Costa Rica journalist;
   (3) climate-health convergence panel — combine UN emission warning
   + Kigali Amendment into one main.
B. Weakest main: Dhoni (#10) — sports retirement, limited global
   impact; swap it for Guinea/Ebola.
C. Craft risk: 12 mains + map + list on 1024x1024 compresses panels
   to ~250px wide; at the judge's 300px review size, decks/tags/map
   dots risk illegibility — mitigate with one bold headline + one-line
   fact, type >=14pt, simpler icons, or cut to 10 mains.

## What I took

- TAKE (A1): add Ebola (DR Congo) as main #13 (AFRICA). My 12 mains
  had zero Africa — a real breadth gap against judge criterion 2.
  Verified 2026-11-18 ~15:15 WIB: 11,376 confirmed cases, 5,568
  deaths through 14 Nov (ECDC / WHO / Reuters, reported 17 Nov);
  latest update 11,432 cases / 5,593 deaths through 15 Nov.
  Africa CDC director Jean Kaseya: outbreak "remains out of control"
  six months in. Deck: "Cases pass 11,000 and deaths 5,500; Africa
  CDC says the outbreak is out of control." 13 mains is within the
  observed top-5 range (top 4 has 15).
- TAKE (C, as a constraint): strict deck brevity — max 2 short lines
  (~90 chars), bold headline, tags short; check the render at 300px
  wide before finalizing. NOT taking the "cut to 10 mains" part:
  top posters run 9–15 mains; cutting mains would lose consensus
  stories.

## What I rejected, and why

- REJECT (B): dropping Dhoni. Dhoni is a main in 4 of the top 5
  posters — that is empirical evidence from the actual judge, which
  outweighs the model's theoretical ranking. Sports breadth is part
  of the winning formula, and the top posters also place Dhoni late
  (#9–11), so the ordering is the formula, not a flaw. Fix the
  Africa gap by ADDING Ebola, not by removing a consensus main.
- REJECT (A3): combo climate panel. Merging two unrelated items
  (UN emission warning + Kigali Amendment) into one panel muddies
  readability (criterion 3: each story clear from its picture).
  Both stay in the also-on list separately.
- REJECT (A2): promoting Costa Rica journalist to a main. Real story
  (in top 2's also-on) but much weaker news value than the 13 mains;
  a single murder cannot displace a consensus main. Stays in also-on.
- NOTE: the model's first (truncated) reply wrongly claimed "Top 5
  all have an Africa story" and "Top 5 never omit the hemisphere" —
  false; I viewed the posters myself and only top 3 has an Africa
  main (Guinea). The model never saw the posters; its claims about
  their contents are not evidence. Its specific story suggestions
  (e.g. "Lula signs Amazon decree") were unverified inventions —
  none were used without a live source check.
