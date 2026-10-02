---
video_id: tTeMYuS87oU
url: https://www.youtube.com/watch?v=tTeMYuS87oU
title: An Introduction to Hypothesis Testing
channel: jbstatistics
duration: 9:54
language: en
unit: L10
status: OK
---

[00:01] Let's take a look at an introduction to hypothesis testing,
[00:04] an important part of statistical inference.
[00:09] Let's look at an example to start.
[00:10] Suppose our friend Pete claims he can guess the suit of a randomly selected playing card
[00:15] more than one-quarter of the time on average.
[00:17] If one is simply guessing randomly,
[00:19] then there is a one quarter chance or guessing correctly on any given card.
[00:23] And Pete says he does better than this on average.
[00:28] We decide to make Pete back up his claim,
[00:31] and we make Pete guess the suit of a randomly selected card 100 times.
[00:35] So if Pete is purely guessing, on average he'll get 25 correct.
[00:39] And he guesses correctly 28 times,
[00:42] and he might be happy about that and say that that shows that he was correct.
[00:45] But does this really provide strong evidence that Pete has a probability of
[00:50] greater than one-quarter of correctly guessing the suit of a card?
[00:57] If Pete is simply guessing randomly,
[01:00] then on any individual card, he has a one-quarter chance of getting it correct.
[01:04] And the number of correct guesses in 100 would follow a binomial distribution.
[01:08] with parameters n=100 and p=1/4.
[01:12] And that binomial distribution is given here.
[01:15] It is the distribution of the number correct if someone is purely guessing at
[01:20] the suits of 100 randomly selected playing cards.
[01:24] Here the possible values go all the way out to 100,
[01:28] but the probabilities get pretty small so I've chopped it off here at 50,
[01:31] just to make the plot look a little nicer.
[01:36] And we might ask ourselves this question:
[01:39] what is the probability of getting 28 or more correct when guessing randomly?
[01:44] Pete actually got 28 correct
[01:47] but had he done even better, gotten even more correct,
[01:50] we would have thought that was even greater evidence in favour of his claim.
[01:57] And so we're going to work out the probability that Pete would do as well as he did,
[02:01] or even better, if he's simply randomly guessing.
[02:05] And so, we could use the binomial formula,
[02:08] or I sped things up a little bit using software.
[02:11] So if X is a random variable with this distribution,
[02:15] the probability that the random variable takes on a value
[02:18] bigger than or equal to 28 is approximately 0.278.
[02:27] So if Pete has a one-quarter chance of guessing correctly on any given card,
[02:31] the probability that he'd do as well as he did or even better, is approximately 0.278.
[02:40] And that probability is not very small,
[02:44] so it is not unlikely to get this many correct due to chance.
[02:47] And so we would say that there is not strong evidence
[02:51] that Pete has better than a one-quarter chance of correctly guessing the suit.
[02:58] We just informally conducted a hypothesis test of the null hypothesis that p is equal to 1/4.
[03:04] Or in other words, that Pete does just the same as someone who is randomly guessing.
[03:10] And we tested that against the alternative hypothesis that p is greater than 1/4.
[03:15] Or in other words, that on average Pete does better than someone who is simply purely guessing.
[03:22] And based on what we saw
[03:24] we did not have strong evidence against this null hypothesis.
[03:32] But suppose instead Pete had guessed correctly 44 times.
[03:36] 44 is way out here, a very unlikely value to get if one is simply randomly guessing.
[03:42] And the probability of doing as well as that or even better,
[03:48] the probability that a random variable with this distribution
[03:52] takes on a value that's greater than or equal to 44, is 0.000027.
[03:59] And that is approximately one time in 37,000,
[04:06] so it would be very very unlikely
[04:08] to do as well as Pete did or better
[04:12] if he is simply randomly guessing.
[04:17] Since this probability is very low, one of two things occurred:
[04:21] Pete is simply guessing, with a probability of success of 1/4,
[04:25] and we witnessed a very unusual event due to chance,
[04:28] or Pete is truly guessing the suit more often than one-quarter of the time on average.
[04:34] Or in other words, the null hypothesis is true and we witnessed a very unusual event,
[04:42] or the null hypothesis is false.
[04:47] Now this doesn't have to mean that Pete has ESP or something like that,
[04:51] it could be something simpler like we've designed our experiment poorly
[04:54] and we're inadvertently giving away information when we look at the card
[04:57] or Pete has a friend a standing behind us signaling him sometimes.
[05:01] But regardless, we have some strong evidence against this null hypothesis.
[05:10] In general, in hypothesis testing we turn a question of interest
[05:14] into hypotheses about the value of a parameter (or parameters).
[05:19] We create a null hypothesis, denoted by H_0,
[05:22] and an alternative hypothesis denoted by H_a.
[05:27] This null hypothesis is sometimes called the status quo hypothesis.
[05:32] It is the hypothesis of no effect, or no difference.
[05:37] The alternative hypothesis is sometimes called the research hypothesis,
[05:42] because it is often the hypothesis that the researcher is trying to show.
[05:46] These ideas are little bit abstract off the start,
[05:51] but it becomes much clearer as we work through examples.
[05:56] Then we calculate an appropriate test statistic, that is based on sample data,
[06:01] and determine how much evidence that gives us against the null hypothesis.
[06:06] And if the evidence against the null hypothesis is strong enough,
[06:10] if it meets a certain significance level,
[06:13] we can reject the null hypothesis in favour of the alternative hypothesis.
[06:19] We might also say that the evidence against the null hypothesis is significant.
[06:27] We might be interested in the question: do men and women have different average
[06:31] salaries after graduating University?
[06:35] Here the appropriate null hypothesis would be that there is no difference,
[06:39] or in other words, the true mean for males is equal to the true mean for females.
[06:43] And the alternative hypothesis is that the null hypothesis is wrong,
[06:47] or that there is a difference between males and females.
[06:51] Now we might phrase that alternative hypothesis a little bit differently
[06:54] depending on the setting, more details on that later on.
[07:01] An important point to note is that we make hypotheses about parameters
[07:05] and never about statistics.
[07:07] So you should never see something like
[07:10] this: that X bar for males is equal to X bar for females.
[07:17] The only place you should see something like that
[07:19] is in a video explaining that you will never see anything like that.
[07:23] We make hypotheses about parameters, and not about statistics.
[07:32] Or we might be interested in a question like:
[07:34] do three different production processes all have the same variance?
[07:38] So the null hypothesis is going to be that there is no difference.
[07:42] That those three population variances are all equal,
[07:46] and the alternative hypothesis is going to be that that is wrong,
[07:50] that those three population variances are not all equal.
[07:57] Or we might be interested in this question.
[08:00] Is the average weight of a certain type of candy bar different from the desired 58 grams?
[08:04] The null hypothesis would be that the true mean is equal to 58 grams.
[08:10] And the alternative hypothesis might be that the true mean is different from 58 grams.
[08:15] Depending on the setting we might choose a different alternative hypothesis,
[08:20] We might choose the alternative hypothesis that mu is actually greater than 58.
[08:28] Or in a different type of situation we might choose
[08:31] the alternative hypothesis that mu is actually less than 58.
[08:36] The appropriate choice of alternative hypothesis depends on the setting,
[08:40] and we'll look at a few examples of that little later on.
[08:47] But many questions remain that could not be answered in this brief introduction.
[08:50] For a given problem, what are the appropriate hypotheses?
[08:53] What is an appropriate test statistic to use?
[08:57] What is an appropriate significance level?
[09:00] When will we say that there is significant evidence against the null hypothesis?
[09:06] And does our data give us significant evidence against the null hypothesis?
[09:11] We're going to use two approaches and hypothesis testing to answer that question:
[09:16] the rejection region approach and the p-value approach. Much more on that later.
[09:21] And what is an appropriate conclusion to the practical problem at hand?
[09:25] In the end we want to tie this in to the questions we are trying to answer.
[09:29] In this video our conclusion simply would have been
[09:32] Pete, we do not have strong evidence that you are doing better
[09:36] than someone who is simply randomly guessing.
[09:40] Coming up with the appropriate conclusion in the end is very very important,
[09:44] as the whole idea here is that we're trying to answer some questions of interest.
