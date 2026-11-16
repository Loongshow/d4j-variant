## Reading and advancement decision

Screening ran the five mandated designs (`ADV-DEPTH-01`, `ADV-REGISTRY-01`, `ADV-LEX-01`, `ADV-OVERLOAD-01`, `ADV-OWNER-01`) three
times each on claude-sonnet-4-6 (primary weaker model) and claude-haiku-4-5 (much weaker), then the two critic-top designs
built afterwards (`ADV-DEFINER-01`, `ADV-MASK-01`) under the same rule. Advancement used the pre-stated criterion: the three
attacks with the lowest Acc@1 over all attempts on the primary weaker model, ties broken by MRR.

- `ADV-DEFINER-01` and `ADV-MASK-01` gave Sonnet 0/3 each (every answered run wrong, or no answer) and Haiku 0/3 each.
- `ADV-LEX-01` gave Sonnet one wrong ranking (decoy first), one right, one timeout.
- `ADV-DEPTH-01` gave Sonnet one right and two timeouts: the only answered run found the gold, so its low all-attempts score
  is exhaustion, not misattribution; it was not advanced.
- `ADV-REGISTRY-01`, `ADV-OVERLOAD-01`, `ADV-OWNER-01`: every answered Sonnet run correct (3/3 each). Haiku's misses on them are
  budget exhaustion with an empty ranking, the same behaviour it shows on the plain control variant.

Advanced to confirmation: `ADV-DEFINER-01`, `ADV-MASK-01`, `ADV-LEX-01`. Haiku was used as the screening "much weaker" model
only; its exhaustion rate made it uninformative for confirmation, and the brief's confirmation sample (n=10 weaker, n=5 Opus)
was run on Sonnet and Opus. The plain control variant (`CONVERSION-LONG-TREATMENT-01`, attack id `BASE-LONG`) was run three
times on Haiku and ten times on Sonnet to measure baseline exhaustion under the same protocol.

**What confirmation later showed about the screening sample.** Three runs per attack was enough to separate the two attacks that
broke Sonnet completely (`ADV-DEFINER-01`, `ADV-MASK-01`: still 0 hits at n=10) from the ones that did not, but the `ADV-LEX-01`
signal (one wrong ranking in two answers) was a small-sample artefact: at n=10 Sonnet put the gold first in five of six answers. A
three-run screen can rank attacks; it cannot certify a moderate effect.
