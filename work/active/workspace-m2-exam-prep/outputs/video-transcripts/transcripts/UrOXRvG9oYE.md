---
video_id: UrOXRvG9oYE
url: https://www.youtube.com/watch?v=UrOXRvG9oYE
title: Overview of Some Discrete Probability Distributions (Binomial,Geometric,Hypergeometric,Poisson,NegB)
channel: jbstatistics
duration: 6:21
language: en
unit: L07
status: OK
---

[00:01] Let's look at a quick overview of some discrete probability distributions and their relationships.
[00:05] I intend this video to be used as a recap
[00:08] after having been introduced to these distributions,
[00:10] but it could possibly be used as an introductory overview.
[00:14] I don't any calculations in this video,
[00:16] nor do I discuss how to calculate the probabilities.
[00:19] I simply discuss how these different distributions arise,
[00:21] and the relationships between them.
[00:25] The Bernoulli distribution is the distribution of the number of successes on a single Bernoulli trial.
[00:31] In a Bernoulli trial we get either a success or a failure.
[00:34] It's like an answer to a yes or no question.
[00:37] A Bernoulli random variable can take on only the values 0 and 1.
[00:42] For example, we can use the Bernoulli distribution to answer questions like:
[00:46] if a single coin is tossed once, what is the probability it comes up heads?
[00:50] Or, if a single adult American is randomly selected,
[00:54] what is the probability they are a heart surgeon?
[00:58] Some other important distributions are built on the notion of independent Bernoulli trials,
[01:03] where we have a series of trials,
[01:04] and each one results in a success or a failure.
[01:07] An important one is the binomial distribution,
[01:10] which is the distribution of the number of successes in n independent Bernoulli trials.
[01:15] For example, with the binomial distribution we can answer a question like:
[01:19] if a coin is tossed 20 times, what is the probability heads comes up exactly 14 times?
[01:25] And since the binomial distribution is the distribution of
[01:28] the number of successes in n independent Bernoulli trials,
[01:32] the Bernoulli distribution is a special case of the binomial distribution with n=1, a single trial.
[01:40] Continuing on with the theme of independent Bernoulli trials,
[01:43] the geometric distribution is the distribution of the number of trials needed to get the first success.
[01:49] For example, with the geometric distribution we can answer a question like:
[01:53] if a coin has repeatedly tossed, what is the probability
[01:56] the first time heads appears occurs on the 8 toss?
[02:01] The negative binomial distribution is a generalization of the geometric distribution.
[02:06] The negative binomial distribution is the distribution of the number of trials
[02:10] needed to get a certain number of successes in repeated independent Bernoulli trials.
[02:16] So the negative binomial distribution can help us answer questions like:
[02:19] if a coin has repeatedly tossed, what is the probability
[02:23] the third time heads appears occurs on the ninth trial?
[02:29] The way the binomial distribution and the negative binomial distribution arise
[02:33] can sound similar, and they can sometimes be confused.
[02:36] They differ in what the random variable is.
[02:39] In the binomial distribution, the number of trials is fixed,
[02:43] and the number of successes is a random variable.
[02:46] For instance, we're tossing a coin a fixed number of times,
[02:49] and the number of heads that comes up is a random variable.
[02:52] In the negative binomial distribution, the number of successes is fixed,
[02:57] and the number of trials required to get that number of successes is the random variable.
[03:02] For instance, we might be tossing a coin until we get heads 4 times.
[03:06] And the number of tosses required to get heads 4 times is the random variable.
[03:13] Now I'll talk about two distributions that are related to the binomial,
[03:17] but aren't based on independent Bernoulli trials.
[03:20] The hypergeometric distribution is similar to the binomial distribution
[03:24] in that we're interested in the number of successes in n trials,
[03:28] but it's different because the trials are not independent.
[03:31] The hypergeometric distribution is the distribution of the number of successes
[03:36] when we are drawing without replacement from a source that contains
[03:39] a certain number of successes and a certain number of failures.
[03:43] For example, we can use the hypergeometric distribution to answer a question like:
[03:48] if 5 cards are drawn without replacement from a well shuffled deck,
[03:51] what is the probability exactly 3 hearts are drawn?
[03:55] It's different from the binomial because the probability of success,
[03:58] the probability of getting a heart, would change from card to card,
[04:02] depending on what happened before.
[04:04] However, if the cards are drawn with replacement,
[04:07] meaning the card was put back in and reshuffled before the next card was drawn,
[04:11] then the trials would be independent and we would use the binomial distribution instead.
[04:18] If we are sampling only a small fraction of objects without replacement from a large population
[04:23] then the trials are still not independent, but that dependency has only a small effect,
[04:28] and the binomial distribution closely approximates the hypergeometric distribution.
[04:32] So there are times when a problem is in its nature a hypergeometric problem,
[04:36] but we use the binomial distribution as an approximation.
[04:40] This can make our life a little bit easier sometimes.
[04:44] Another distribution related to the binomial is the Poisson distribution.
[04:48] But this one's a little harder to explain.
[04:50] The Poisson distribution is the distribution of the number of events
[04:54] in a given time or length, or area, or volume etc.,
[04:58] if those events are occurring randomly and independently.
[05:02] There's a bit more to it than that, and I go into this in much greater detail in my Poisson videos.
[05:07] But that's the gist of it. So we might use the Poisson distribution to answer a question like:
[05:12] what is the probability there will be exactly 4 car accidents
[05:15] on a certain university campus in a given week?
[05:20] There is a relationship between the Poisson distribution and the binomial distribution.
[05:25] The Poisson distribution closely approximates the binomial distribution
[05:29] if n, the number of trials, in the binomial, is large
[05:32] and p, the probability of success, is very small.
[05:36] So suppose we have a question like:
[05:38] what is the probability that in a random sample 100,000 births,
[05:41] there is at least one case of progeria?
[05:44] Progeria is an extremely rare disease that causes premature aging,
[05:48] and it occurs in about 1 in every eight million births.
[05:52] This is truly a binomial problem. But we have a binomial problem
[05:56] with a very large n, 100,000,
[05:58] and a very small probability of success, 1 in eight million or so,
[06:02] because progeria such a rare disease.
[06:05] And so this could be very well approximated by the Poisson distribution.
[06:10] I look into all of these concepts discussed in this video in greater detail
[06:13] in the videos for these specific distributions.
