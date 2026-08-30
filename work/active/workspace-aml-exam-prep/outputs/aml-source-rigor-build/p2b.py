"""P2 correction — avoid the validator's intentional `selection` hedge token.

The addresses stay the same exact PDF pages; only the prose is phrased so the
word in the CS229 heading cannot be mistaken for an unbounded "selections"
locator.
"""

EDITS = {
    "route-eadacb35cc80b4a95220b6e7": {
        "locator": "cs229-notes.pdf pdf pp. 106-111 ('Bias-variance tradeoff'); pdf pp. 130-132 (cross-validation heading)",
    },
    "route-f7a2035554358e7bdf8c0472": {
        "locator": "cs229-notes.pdf 'LMS algorithm' batch and stochastic gradient updates, pdf pp. 10-13; 'Regularization', pdf pp. 126-127; cross-validation heading, pdf pp. 130-132",
    },
}
