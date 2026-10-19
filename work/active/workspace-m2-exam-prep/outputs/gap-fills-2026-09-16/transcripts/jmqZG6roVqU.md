---
video_id: jmqZG6roVqU
url: https://www.youtube.com/watch?v=jmqZG6roVqU
title: An Introduction to the Poisson Distribution
channel: jbstatistics
duration: 9:03
language: en
unit: L07
status: OK
---

[00:02] Let's look at an introduction to the Poisson distribution,
[00:04] an important discrete probability distribution.
[00:08] Suppose we are counting the number of occurrences of an event
[00:11] in a given unit of time or distance or area or volume.
[00:14] For example, we might be counting up the number of car accidents in a day,
[00:17] in a city like Toronto perhaps.
[00:19] Or the number of dandelions in a square metre plot of land.
[00:22] Then the number of events is going to be a random variable
[00:26] that may or may not have the Poisson distribution,
[00:28] depending on the specifics of the situation.
[00:30] But a Poisson random variable is a count of the number of occurrences of an event.
[00:37] I'm going to phrase the following in terms of time,
[00:40] but the same ideas hold if we are discussing distance or area or volume etc.
[00:44] Suppose events are occurring independently.
[00:47] In other words, knowing when one event happens
[00:49] gives absolutely no information about when another event will occur.
[00:52] And the probability that an event occurs in a given length of time does not change through time.
[00:58] In other words, the theoretical rate at which the events are occurring
[01:01] does not change through time.
[01:03] A little more loosely we might say that the events are occurring randomly and independently.
[01:11] If these conditions hold, then the random variable X,
[01:13] which represents the number of events in a fixed unit of time,
[01:17] has the Poisson distribution.
[01:20] Here's the probability mass function for the Poisson distribution,
[01:23] what we'll use to calculate probabilities.
[01:26] The probability the random variable X takes on the value little x,
[01:30] which you'll sometimes see written as p(x),
[01:34] is equal to lambda^x times e^(-lambda) over x!
[01:40] e, like pi, is an important mathematical constant, the base of natural logarithms.
[01:47] It is approximately 2.71828, but it is an irrational number
[01:54] that has infinite non-repeating decimal places.
[01:57] We've discussed factorials previously, but as a specific example of this x!,
[02:03] 5! would be 5 times 4 times 3 times 2 times 1,
[02:11] and that would be 120.
[02:13] It's not a probability distribution until we say what values X can take on.
[02:18] Here the random variable is a count of the number of events in a given unit of time,
[02:23] and so it can take on any non-negative whole number value.
[02:26] So this is the probability mass function that we use to calculate probabilities
[02:31] for any value of x that's 0,1, 2, off to infinity.
[02:38] There is no upper bound on the value that X can take on.
[02:42] But depending on the situation the probabilities eventually
[02:45] get tiny for large values of X.
[02:48] The mean of the Poisson distribution is lambda.
[02:51] So mu, the mean of the random variable X, is equal to lambda.
[02:56] So we could have used mu as our parameter, and some sources do that.
[02:59] But we often use lambda for the Poisson distribution.
[03:02] The variance of the Poisson distribution,
[03:05] which we'll label as sigma squared, is also equal to lambda.
[03:09] For the Poisson distribution, the mean and the variance are equal.
[03:14] Let's look at an example.
[03:17] Plutonium-239 is an isotope of plutonium that is used in nuclear weapons and reactors.
[03:23] One nanogram, or 1 billionth of a gram, of plutonium 239
[03:28] will have an average of 2.3 radioactive decays per second.
[03:31] And the number of decays in a given period will follow,
[03:34] to a very close approximation, a Poisson distribution.
[03:37] Here we'd like to know: what is the probability that in a
[03:40] randomly selected two second period there are exactly 3 radioactive decays?
[03:46] We'll let the random variable X
[03:47] represent the number of decays in a two second period.
[03:51] Lambda is the mean number of decays in that period.
[03:55] So here we have an average of 2.3 radioactive decays per second,
[04:00] but we're talking about a two second period
[04:03] and so in that period, the mean number of occurrences,
[04:06] which is going to equal lambda, is going to be 2.3 times 2, which is 4.6.
[04:13] And so X has a Poisson distribution with lambda equal to 4.6.
[04:19] We want to find the probability that the random variable X takes on the value 3.
[04:25] And the Poisson probability mass function
[04:28] is lambda^x times e to the minus lambda, over x!
[04:34] And here that's going to be
[04:35] 4.6, lambda, raised to the third power
[04:39] times e to the -4.6 divided by 3!
[04:45] If we worked that out on a calculator or computer
[04:48] we'd see that's equal to 0.163, when rounded to three decimal places.
[04:54] So that is the probability of getting exactly three radioactive decays in a two second period.
[05:02] If we were to calculate the probabilities for the
[05:04] different possible values of X and plot them, we'd get this.
[05:08] This is the probability distribution of the random variable X in this spot,
[05:11] a Poisson distribution with lambda equal to 4.6.
[05:15] The number we calculated, the probability that X takes on the value 3, is here.
[05:21] That's what we just calculated to be 0.163.
[05:28] We can see here that X takes on the possible values 0, 1, 2, on up.
[05:33] I've truncated the plot over here at 15,
[05:36] since the possible values go off to infinity,
[05:39] but the probabilities start getting very very small.
[05:42] But for a Poisson distribution there is no upper bound
[05:45] on the values the random variable X can take on.
[05:49] For this distribution, the mean mu is equal to lambda, and that's 4.6 here.
[05:55] The variance is also equal to lambda, so that's also equal to 4.6
[06:01] And if we wanted the standard deviation sigma, we'd simply take the square root of 4.6.
[06:08] If we look closely we can see that there's a hint of right-skewness in this distribution.
[06:12] The Poisson distribution has some right skewness,
[06:14] but it depends on the value of lambda.
[06:16] When lambda is large, the distribution will be close to symmetric,
[06:20] when lambda is close to 0, the right skewness can be pretty strong.
[06:25] Suppose we wanted a different probability,
[06:28] the probability there are no more than three radioactive decays.
[06:32] Here that's the red bit on the plot.
[06:34] We'd need to work out the probability of 0, of 1, of 2, and of 3
[06:40] using the Poisson probability mass function,
[06:43] and add them together. So let's go ahead and do that.
[06:48] Here we need to find the probability that the random variable X
[06:51] takes on a value less than or equal to 3,
[06:53] which is the sum up the probabilities of 0, 1, 2, and 3.
[06:58] We put these values of x
[07:00] into the Poisson probability mass function with a lambda of 4.6,
[07:06] and when rounded to three decimal places,
[07:08] these probabilities work to these 4 values,
[07:11] and they sum to 0.326.
[07:14] Working out probabilities like this can be a bit of a pain if there are a lot of values,
[07:18] so we often rely on software to carry out the calculations.
[07:24] There is an important relationship that sometimes helps us determine
[07:27] whether a random variable has a Poisson distribution.
[07:30] The binomial distribution tends toward the Poisson distribution
[07:34] as n tends to infinity, p tends to 0 and np stays constant.
[07:38] For us, at the moment, the important bit is that the Poisson distribution
[07:42] with lambda equal to np from the binomial distribution,
[07:46] closely approximates the binomial distribution if n is large and p is small.
[07:52] In fact, this is why the radioactive decays of plutonium has a Poisson distribution.
[07:57] Even for a tiny bit a plutonium, there are a very large number of atoms,
[08:01] and each one has a tiny probability of experiencing a radioactive decay in a two second period.
[08:06] So in the example we just worked through,
[08:09] it was in its underlying nature a binomial problem
[08:12] with a very large n and a very small p.
[08:15] And that's why the number of radioactive decays
[08:17] is very well approximated by the Poisson distribution.
[08:20] I have videos that explore this relationship in greater detail.
[08:27] Like many models in probability and statistics,
[08:30] the Poisson distribution is typically used as an approximation to the true underlying reality.
[08:35] In most situations where we use the Poisson,
[08:38] we know that the Poisson distribution doesn't fit the scenario precisely
[08:41] but we use it as an approximation. Possibly a very good approximation.
[08:46] But it can be difficult to determine whether
[08:48] a random variable has a Poisson distribution to a reasonable approximation.
[08:53] So I'm going to look at a few examples and discuss some considerations in another video.
