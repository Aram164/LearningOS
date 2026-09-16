---
video_id: eexQyHj6hEA
url: https://www.youtube.com/watch?v=eexQyHj6hEA
title: The Relationship Between the Binomial and Poisson Distributions
channel: jbstatistics
duration: 5:23
language: en
unit: L07
status: OK
---

[00:01] Let's take a look at the relationship between the binomial and Poisson distributions.
[00:06] The binomial distribution tends toward the Poisson distribution
[00:10] as n tends to infinity, p goes to zero
[00:13] and lambda = np stays constant.
[00:19] Here we have the binomial formula and the Poisson formula
[00:21] Now we know the mean of a binomial random variable is np
[00:26] and we know that the mean of a Poisson random variable is lambda,
[00:29] so if we set n times p equal to lambda,
[00:34] and then p equals lambda over n,
[00:37] and we took this value and we substituted it in for p up here,
[00:42] then, it might not be obvious,
[00:45] but as n gets really large, as n goes off to infinity,
[00:48] this binomial formula tends towards this Poisson
[00:52] so as n goes off to infinity and p goes to 0
[00:58] because lambda equals np is a constant
[01:01] as that happens the binomial tends toward the Poisson.
[01:05] Now it's not obvious, but I do have a mathematical proof that in another video.
[01:10] An implication of this is that the Poisson distribution can be used to provide a
[01:14] reasonable approximation to the binomial distribution if n is large and p is small.
[01:21] Let's look at an example to illustrate.
[01:22] Albinism is a rare genetic disorder that affects approximately 1 in 20,000 Europeans.
[01:27] This 1 in 20,000 is just an approximate value
[01:31] but let's take it to be exact for the purposes of this question.
[01:34] People with albinism produce little or none of the pigment melanin, but this manifests itself in different ways.
[01:40] Overall they tend to have very fair skin
[01:42] and very light colored hair, and things along these lines.
[01:46] In a random sample of 1,000 Europeans,
[01:49] what is the probability that exactly 2 have albiniism?
[01:53] Well we're looking at 1,000 people,
[01:55] each individual person either has Albinism or they do not,
[01:59] and if we are sampling randomly and independently,
[02:03] then this is really going to follow a binomial distribution,
[02:07] the number that have albinism is going to have a binomial distribution
[02:11] with n of 1000
[02:14] and p is the probability any one individual person has it.
[02:17] And that was given on the last page as 1/20,000.
[02:21] And we are interested in the probability that X is equal to 2.
[02:25] And so we just use a binomial formula,
[02:28] n choose x, so 1000 choose 2,
[02:33] times p to the x, 1/20,000 squared,
[02:37] times 1-p, 1 -1/20,000 to the n-x, so 1000-2.
[02:47] And if you put that into your calculator
[02:49] we get 0.001187965.
[02:56] Now let's use the Poisson approximation in this case, just to see how well it works in this particular scenario.
[03:02] We would let lambda equal np,
[03:05] which is one thousand times 1/20,000,
[03:10] which works out to 1 in 20, or 0.05.
[03:13] Then our Poisson formula is lambda to the x,
[03:17] e to the minus lambda, over x! [factorial]
[03:20] So if we want the probability that X is equal to 2 using our Poisson approximation,
[03:25] this is going to be approximately
[03:27] 0.05, lambda, to the x,
[03:30] e to the minus lambda over x factorial.
[03:36] Put that into your calculator or computer
[03:39] and you'd see that this is equal to 0.001189037.
[03:46] And the value we get from the Poisson approximation is very close
[03:51] to the true value from the binomial distribution.
[03:53] That's true in this case because we had such a large n and a very small p,
[03:59] so the Poisson approximation is going to be very reasonable in this particular case.
[04:05] Here's a very rough guideline. The Poisson approximation is reasonable
[04:08] if n is greater than 50 and np is less than 5.
[04:12] But this is just a rough guideline, the approximation is going to work best
[04:15] when n is a really big and p is really close to zero.
[04:20] So whether it's a reasonable approximation or not depends on your needs,
[04:24] but this is one rough guideline one could use.
[04:27] Why use this approximation? If something truly has a binomial distribution
[04:31] then we should calculate probabilities based on the binomial distribution.
[04:34] But sometimes those factorials and exponentials in the binomial formula
[04:38] can become problematic to calculate.
[04:40] If n is very large we might end up getting some round off error
[04:43] or a computer or calculator might actually just give us an error
[04:47] and say it can't calculate it.
[04:48] That's a little bit less of an issue for the Poisson distribution.
[04:51] Also a problem maybe binomial conceptually, but n and p may not be known.
[04:56] In order to calculate binomial probabilities, we need to know n and p.
[05:01] Now if we happen to know the mean number of occurrences,
[05:04] we could call that lambda and use that in  a Poisson formula,
[05:08] provided we knew we had a very large n and a very small p,
[05:13] But we don't need to know what those actual values are,
[05:16] we just need to know the mean number of occurrences.
