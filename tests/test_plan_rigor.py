from tools.learning_os.rules.plan_rigor import _has_unquoted_hedge


def test_exact_title_may_contain_selection_word():
    locator = (
        "Spring 2022 playlist, Lecture 10 "
        "'Bias/Variance, Regularization, and Model Selection'"
    )
    assert not _has_unquoted_hedge(locator)


def test_unquoted_selection_instruction_remains_vague():
    locator = "Lecture 10 'Model Selection' — selected chapters"
    assert _has_unquoted_hedge(locator)
