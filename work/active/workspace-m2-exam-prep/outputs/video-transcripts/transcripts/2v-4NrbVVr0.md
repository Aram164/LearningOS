---
video_id: 2v-4NrbVVr0
url: https://www.youtube.com/watch?v=2v-4NrbVVr0
title: Zufall ohne Gedächtnis: Geometrische & Exponentialverteilung endlich verstehen (mit Alwin ☕)
channel: Kurzes Tutorium Statistik
duration: 11:53
language: en
unit: L07
status: OK
---

[00:03] In this video I explain two probability distributions:
[00:06] probability distributions: the geometric distribution and
[00:09] the geometric distribution and the exponential distribution.
[00:11] the exponential distribution. We already know that
[00:13] We already know that random variables
[00:15] random variables assign probabilities to possible numerical values. This is exactly what
[00:18] assign probabilities to possible numerical values. This is exactly what
[00:20] probability distributions, such as the geometric or
[00:23] the geometric or exponential distribution, are about.
[00:25] exponential distribution, are about. However, such models attempt
[00:29] to develop general rules and formulas for certain recurring patterns .
[00:33] . We'll see how that works at
[00:35] We'll see how that works at Alwin's restaurant.
[00:37] Alwin's restaurant. Alwin is currently looking for
[00:39] Alwin is currently looking for a great new coffee. He tastes
[00:43] a great new coffee. He tastes different samples one after the other
[00:45] different samples one after the other until he finds a coffee
[00:47] until he finds a coffee that completely
[00:49] that completely convinces him.
[00:51] convinces him. More generally, we could now ask:
[00:54] More generally, we could now ask: how many samples does he have to try before
[00:56] how many samples does he have to try before he finds his perfect coffee?
[00:59] he finds his perfect coffee? Or, to be more precise, what is the
[01:01] Or, to be more precise, what is the probability that he found his coffee after 10, 15,
[01:04] probability that he found his coffee after 10, 15, 20, or generally x number of cups
[01:08] 20, or generally x number of cups ? Let's assume
[01:11] ? Let's assume that a
[01:12] that a randomly selected coffee has a
[01:14] randomly selected coffee has a 10% probability of completely
[01:17] 10% probability of completely convincing him. This means that there is a
[01:20] convincing him. This means that there is a 90% probability that a
[01:23] 90% probability that a coffee will not meet your requirements.
[01:26] coffee will not meet your requirements. Then we could imagine the following series
[01:28] Then we could imagine the following series . The first cup of coffee tastes
[01:30] . The first cup of coffee tastes bad, 90%. [music]
[01:32] bad, 90%. [music] Second coffee doesn't help either, 90%. And so on,
[01:36] Second coffee doesn't help either, 90%. And so on, until perhaps on the fifth
[01:38] until perhaps on the fifth try he finds a coffee he
[01:40] try he finds a coffee he likes. The probability is
[01:42] likes. The probability is 10%. The fact that
[01:45] 10%. The fact that every coffee has the same
[01:47] every coffee has the same probability of tasting good
[01:48] probability of tasting good implies that the coffees
[01:51] implies that the coffees are independent of each other. Whether he is
[01:54] are independent of each other. Whether he is convinced by the second coffee does
[01:56] convinced by the second coffee does not depend on how the previous coffee
[01:59] not depend on how the previous coffee was.
[02:00] was. This independence also means
[02:03] This independence also means that we can multiply the individual probabilities
[02:05] that we can multiply the individual probabilities [music] to arrive at
[02:07] [music] to arrive at the overall probability for a
[02:09] the overall probability for a specific tasting outcome.
[02:12] specific tasting outcome. This means that the probability is that
[02:15] This means that the probability is that Alwin
[02:17] Alwin found his perfect [music] coffee on the fifth try. This
[02:19] found his perfect [music] coffee on the fifth try. This results from 0.9* 0.9* 0.9* 0.9* 0.1
[02:24] results from 0.9* 0.9* 0.9* 0.9* 0.1 [music], so 0.9 to the power of 4* 0.1 is approximately 0.066.
[02:33] If we had asked what the probability is that he will like the tenth coffee [music]
[02:36] probability is that he will like the tenth coffee [music] , then we would have
[02:39] , then we would have 0.9 to the power of 9 x 0.1 and that gives approximately
[02:43] 0.9 to the power of 9 x 0.1 and that gives approximately 0.039.
[02:46] If we generally denote the probability of success [music] per
[02:49] probability of success [music] per step with small P and
[02:52] step with small P and
[02:54] ask for the overall probability of success in step [music] x, we obtain the formula 1 - p to the power of x - 1* p.
[03:02] we obtain the formula 1 - p to the power of x - 1* p. Thus, we already have the
[03:04] Thus, we already have the probability function of the
[03:05] probability function of the geometric distribution, which has one
[03:08] geometric distribution, which has one parameter, namely small p. And we
[03:11] parameter, namely small p. And we could now, for example, calculate... If the
[03:13] could now, for example, calculate... If the probability of success per attempt
[03:15] probability of success per attempt [music] = 0.2, then the
[03:18] [music] = 0.2, then the probability that Alwin finds
[03:20] probability that Alwin finds a convincing coffee exactly on the fifth attempt is
[03:22] a convincing coffee exactly on the fifth attempt is 1-0, [music] to the power of 5-1*
[03:26] 1-0, [music] to the power of 5-1* 0,2 and that is approximately 0,082.
[03:32] That's the answer to the question about exactly the fifth coffee. A more
[03:37] exactly the fifth coffee. A more practical question, however, would be
[03:40] practical question, however, would be how likely it is
[03:42] how likely it is that he will be convinced by the fifth coffee at the latest
[03:44] that he will be convinced by the fifth coffee at the latest , because we want to know
[03:46] , because we want to know how extensive the whole thing will be.
[03:49] how extensive the whole thing will be. This calculates the so-called
[03:51] This calculates the so-called distribution function.
[03:53] distribution function. It has the large symbol fg of x and we
[03:56] It has the large symbol fg of x and we could determine the result by adding the
[03:59] could determine the result by adding the individual probabilities of success
[04:01] individual probabilities of success for the first, second, third,
[04:04] for the first, second, third, fourth or fifth cup.
[04:07] fourth or fifth cup. Fortunately, there is a
[04:10] Fortunately, there is a simple formula for this: 1 - 1 - p to the power of x.
[04:16] simple formula for this: 1 - 1 - p to the power of x. Whether I
[04:17] Whether I add the individual probabilities or
[04:20] add the individual probabilities or directly use the formula for large F, the result is
[04:23] directly use the formula for large F, the result is always the same.
[04:29] We now know the two most important formulas of the geometric
[04:33] important formulas of the geometric distribution, namely the
[04:35] distribution, namely the small probability function fg of
[04:37] small probability function fg of x = 1 - p to the power of x - 1* p
[04:43] x = 1 - p to the power of x - 1* p and the large distribution function fg of
[04:46] and the large distribution function fg of x = 1- 1- [music] p to the power of x. And as
[04:51] x = 1- 1- [music] p to the power of x. And as mentioned, the geometric distribution has
[04:53] mentioned, the geometric distribution has one parameter, namely P, the
[04:56] one parameter, namely P, the probability of success per attempt.
[05:00] probability of success per attempt. The question remains: how do I
[05:03] The question remains: how do I actually know how big P is?
[05:06] actually know how big P is? The expected value is helpful here.
[05:08] The expected value is helpful here. If I need an average of 10 attempts
[05:10] If I need an average of 10 attempts until I like a coffee [music]
[05:11] until I like a coffee [music] , then P = one toe. If
[05:15] , then P = one toe. If I need an average of 20 attempts,
[05:18] I need an average of 20 attempts, then [music] P = 20. In
[05:21] then [music] P = 20. In general, P is therefore the reciprocal of the
[05:24] general, P is therefore the reciprocal of the expected value. Most people intuitively find this
[05:27] expected value. Most people intuitively find this logical, but of
[05:29] logical, but of course it can also be
[05:31] course it can also be derived mathematically. I'm not doing that now, it's fine.
[05:33] derived mathematically. I'm not doing that now, it's fine. But
[05:35] But since we're already talking about Alwin,
[05:37] since we're already talking about Alwin, we can take care of another problem
[05:39] we can take care of another problem . Its booking system
[05:42] . Its booking system crashes occasionally. If that
[05:44] crashes occasionally. If that happens, he needs a technician to
[05:46] happens, he needs a technician to restart it. Therefore, the question for him
[05:49] restart it. Therefore, the question for him , now that the system
[05:52] , now that the system has just been repaired, is how long will it be until the
[05:55] has just been repaired, is how long will it be until the next crash?
[05:58] next crash? Actually, it's quite similar to the
[06:00] Actually, it's quite similar to the coffee example, how many times until the first
[06:03] coffee example, how many times until the first success. With one difference:
[06:07] success. With one difference: we took discreet steps while having coffee.
[06:09] we took discreet steps while having coffee. first, second, third, fourth cup and
[06:13] first, second, third, fourth cup and so on. Whereas a [music]
[06:14] so on. Whereas a [music] system failure involves a time span,
[06:17] system failure involves a time span, i.e., a constant quantity. Let's just assume
[06:20] i.e., a constant quantity. Let's just assume we're talking
[06:22] we're talking about a period of 2 months.
[06:26] about a period of 2 months. To build on what we already
[06:28] To build on what we already know, let's imagine this time span
[06:31] know, let's imagine this time span divided into time blocks, e.g. 4.
[06:35] divided into time blocks, e.g. 4. The length of such an interval would
[06:38] The length of such an interval would therefore be small t. The total time span
[06:41] therefore be small t. The total time span divided by 4 gives 0.5 months
[06:44] divided by 4 gives 0.5 months [music]
[06:45] [music] and we call this partial span length
[06:47] and we call this partial span length Delta t.
[06:50] Delta t. The crash could happen at any of these intervals
[06:51] The crash could happen at any of these intervals .
[06:53] . We
[06:54] We again denote the probability of this as small p and
[06:57] again denote the probability of this as small p and imagine that P here would be approximately 0.2.
[07:02] imagine that P here would be approximately 0.2. If we make the blocks smaller
[07:04] If we make the blocks smaller by dividing the entire span into eight
[07:06] by dividing the entire span into eight parts, Delta t becomes 0.25.
[07:10] parts, Delta t becomes 0.25. However, it would then be reasonable
[07:13] However, it would then be reasonable to assume that the
[07:14] to assume that the probability of a crash also decreases in
[07:16] probability of a crash also decreases in each time block [music].
[07:18] each time block [music]. The exact size is a bit
[07:20] The exact size is a bit uncertain, but with a Delta T that is half as long,
[07:22] uncertain, but with a Delta T that is half as long, one could at least
[07:24] one could at least plausibly imagine the probability of
[07:25] plausibly imagine the probability of a crash to be half as large
[07:27] a crash to be half as large , e.g.,
[07:30] , e.g., approximately 0.1 in this case.
[07:34] approximately 0.1 in this case. To generalize this,
[07:35] To generalize this, we consider that the entire time t
[07:38] we consider that the entire time t is divided into x many blocks, each with a
[07:41] is divided into x many blocks, each with a length of Delta t.
[07:44] length of Delta t. Rearranged, x = t dur delta t.
[07:49] Rearranged, x = t dur delta t. The probability of a
[07:50] The probability of a small block P crashing should be at least
[07:52] small block P crashing should be at least [music] approximately proportional to its
[07:54] [music] approximately proportional to its length Delta t.
[07:57] length Delta t. I call this proportionality factor
[07:59] I call this proportionality factor Lambda.
[08:01] Lambda. Now we take the formula we know
[08:04] Now we take the formula we know for the geometric distribution, namely the one
[08:06] for the geometric distribution, namely the one for the distribution function,
[08:09] for the distribution function, and substitute it in.
[08:17] Then we make the intervals increasingly finer by letting Delta t, i.e., the
[08:22] finer by letting Delta t, i.e., the width of the sub-segments, approach zero
[08:24] width of the sub-segments, approach zero . This is how we approach
[08:27] . This is how we approach a continuous timeline.
[08:30] a continuous timeline. Then we would have lambda times a value
[08:32] Then we would have lambda times a value close to 0. Let's say, for example,
[08:35] close to 0. Let's say, for example, 0.001 -
[08:39] this value would be somewhat close to 1. So, let's
[08:43] this value would be somewhat close to 1. So, let's say again, as an example,
[08:45] say again, as an example, 0.99999.
[08:48] However, in the exponent we find a small value t, which is a fixed
[08:53] a small value t, which is a fixed number divided by a number close to 0,
[08:57] number divided by a number close to 0, resulting in a very large number, could
[09:00] resulting in a very large number, could be 400,000 1000, for example. And so
[09:03] be 400,000 1000, for example. And so the question arises, how much is
[09:06] the question arises, how much is a number slightly smaller than 1 raised to the power of a
[09:09] a number slightly smaller than 1 raised to the power of a very large number linked via Delta t
[09:12] very large number linked via Delta t ? In fact, this can even be
[09:15] ? In fact, this can even be shown using high school mathematics [music],
[09:18] shown using high school mathematics [music], but since Alwin doesn't have much time,
[09:20] but since Alwin doesn't have much time, I'll just give you the result. The result is
[09:22] I'll just give you the result. The result is [music] 1 - e raised to the power of - lambda times t
[09:26] [music] 1 - e raised to the power of - lambda times t . And that is the formula for the
[09:29] . And that is the formula for the distribution function.
[09:31] distribution function. the so-called exponential distribution,
[09:35] the so-called exponential distribution, and with this one can, for example, calculate
[09:38] and with this one can, for example, calculate the probability of at
[09:39] the probability of at most one month until the
[09:41] most one month until the next crash. If Lambda
[09:44] next crash. If Lambda were, for example, half a 1, then the
[09:47] were, for example, half a 1, then the probability that the
[09:48] probability that the next system crash at Alwin would
[09:50] next system crash at Alwin would take at most one month is approximately
[09:53] take at most one month is approximately 0.393.
[09:56] 0.393. The question arises again: how large
[09:58] The question arises again: how large is Lambda?
[10:00] is Lambda? Analogous to the geometric
[10:02] Analogous to the geometric distribution, where P 1 is
[10:05] distribution, where P 1 is given by the expected value, here too
[10:07] given by the expected value, here too lambda is 1 divided by the expected value. So, for
[10:10] lambda is 1 divided by the expected value. So, for example, if a system crash occurs on average every two
[10:14] example, if a system crash occurs on average every two months,
[10:16] months, lambda would be ein/H/b.
[10:20] lambda would be ein/H/b. The probability density f is
[10:22] The probability density f is obtained by
[10:24] obtained by differentiating the distribution function,
[10:26] differentiating the distribution function, because the exponential distribution
[10:28] because the exponential distribution is continuous. One calculates directly with
[10:31] is continuous. One calculates directly with no probability.
[10:33] no probability. Instead, small F tells us what the
[10:36] Instead, small F tells us what the curve looks like, whose partial integrals
[10:39] curve looks like, whose partial integrals give us probabilities.
[10:46] In summary, the geometric distribution models the number of
[10:50] distribution models the number of steps to the first success, the
[10:52] steps to the first success, the exponential distribution the
[10:54] exponential distribution the continuous distance, time [music]
[10:57] continuous distance, time [music] amount to the first success.
[11:00] amount to the first success. Both are memoryless models with a
[11:02] Both are memoryless models with a constant rate: discrete with a fixed
[11:05] constant rate: discrete with a fixed success probability
[11:06] success probability Pritt, and continuous with a constant event rate
[11:10] Pritt, and continuous with a constant event rate Lambda per unit of the
[11:13] Lambda per unit of the continuum quantity under consideration.
[11:15] continuum quantity under consideration. We know small F, which in the case of
[11:18] We know small F, which in the case of discrete distributions such as the
[11:19] discrete distributions such as the geometric distribution is the
[11:20] geometric distribution is the probability function
[11:22] probability function and in the continuous case such as the
[11:24] and in the continuous case such as the exponential distribution is the density function,
[11:28] exponential distribution is the density function, as well as large f, which in both
[11:31] as well as large f, which in both cases is called the distribution function,
[11:33] cases is called the distribution function, which always stands for the probability
[11:34] which always stands for the probability that x takes on at most a
[11:36] that x takes on at most a given value, without
[11:39] given value, without exception.
[11:41] exception. Thanks for watching. Please like and
[11:44] Thanks for watching. Please like and subscribe, because if enough people
[11:46] subscribe, because if enough people do, there will be more videos soon.
