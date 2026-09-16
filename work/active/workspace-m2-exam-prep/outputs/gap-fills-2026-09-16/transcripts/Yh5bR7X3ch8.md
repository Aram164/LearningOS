---
video_id: Yh5bR7X3ch8
url: https://www.youtube.com/watch?v=Yh5bR7X3ch8
title: L18.4 The Weak Law of Large Numbers
channel: MIT OpenCourseWare
duration: 7:31
language: en
unit: L06
status: OK
---

[00:01] In this segment we derive and discuss
[00:03] In this segment we derive and discuss the weak law of large numbers. It is a
[00:05] the weak law of large numbers. It is a rather simple result but plays a central
[00:07] rather simple result but plays a central role within probability theory. The
[00:09] role within probability theory. The setting is as follows. We start with
[00:11] setting is as follows. We start with some probability distribution that has a
[00:14] some probability distribution that has a certain mean and variance which we
[00:16] certain mean and variance which we assume to be finite.
[00:19] assume to be finite. We then draw independent random
[00:21] We then draw independent random variables out of this distribution so
[00:24] variables out of this distribution so that these X eyes are independent and
[00:28] that these X eyes are independent and identically distributed IID for short.
[00:32] identically distributed IID for short. What's going on here is that we're
[00:34] What's going on here is that we're carrying out a long experiment during
[00:36] carrying out a long experiment during which all of these random variables are
[00:39] which all of these random variables are drawn.
[00:40] drawn. Once we have drawn N of these random
[00:43] Once we have drawn N of these random variables, we can calculate the average
[00:46] variables, we can calculate the average of the values that have been obtained
[00:48] of the values that have been obtained and this gives us the so-called sample
[00:51] and this gives us the so-called sample mean.
[00:52] mean. Notice that the sample mean is a random
[00:55] Notice that the sample mean is a random variable because it is a function of
[00:57] variable because it is a function of random variables. It should be
[00:59] random variables. It should be
[01:00] random variables. It should be distinguished from the true mean mu
[01:03] distinguished from the true mean mu which is the expected value of the X
[01:05] which is the expected value of the X eyes
[01:06] eyes
[01:07] eyes which is a number. It is not random.
[01:10] which is a number. It is not random. And mu is some kind of average over all
[01:14] And mu is some kind of average over all the possible outcomes of the random
[01:16] the possible outcomes of the random variable X I.
[01:19] variable X I. The sample mean is the simplest and most
[01:21] The sample mean is the simplest and most natural way for trying to estimate the
[01:24] natural way for trying to estimate the true mean and the weak law of large
[01:26] true mean and the weak law of large numbers will provide some support to
[01:28] numbers will provide some support to this notion.
[01:30] this notion. Let us now look at the properties of the
[01:32] Let us now look at the properties of the sample mean. Let us calculate its
[01:34] sample mean. Let us calculate its expectation.
[01:35] expectation. By the way, this object here involves
[01:39] By the way, this object here involves two different kinds of averaging. The
[01:42] two different kinds of averaging. The sample mean averages over the values
[01:45] sample mean averages over the values observed during one long experiment
[01:50] observed during one long experiment whereas the expectation
[01:53] whereas the expectation averages over all possible outcomes of
[01:57] averages over all possible outcomes of this experiment. The expectation is some
[02:00] this experiment. The expectation is some kind of theoretical average because we
[02:02] kind of theoretical average because we do not get to observe all the possible
[02:05] do not get to observe all the possible outcomes of this experiment but the
[02:07] outcomes of this experiment but the sample mean is something that we
[02:09] sample mean is something that we actually calculate on the basis of our
[02:11] actually calculate on the basis of our observations.
[02:13] observations. In any case, the expected value of the
[02:15] In any case, the expected value of the sample mean by linearity, it is the
[02:19] sample mean by linearity, it is the expected value of the numerator
[02:24] expected value of the numerator divided by the denominator.
[02:27] divided by the denominator. Using linearity once more, the expected
[02:30] Using linearity once more, the expected value of a sum is the sum of the
[02:31] value of a sum is the sum of the expected values and since each one of
[02:33] expected values and since each one of those expected values is equal to mu, we
[02:36] those expected values is equal to mu, we obtain n times mu divided by n which
[02:40] obtain n times mu divided by n which leaves us with mu.
[02:42] leaves us with mu. So, the theoretical average, the
[02:45] So, the theoretical average, the expected value of the sample mean is
[02:47] expected value of the sample mean is equal to the true mean.
[02:49] equal to the true mean. Let us now calculate the variance of the
[02:52] Let us now calculate the variance of the sample mean.
[02:53] sample mean.
[02:54] sample mean. The variance
[02:55] The variance of a random variable divided by a number
[02:59] of a random variable divided by a number is the variance of that random variable
[03:02] is the variance of that random variable divided by the square of that number.
[03:11] Now, since the X eyes are independent,
[03:13] Now, since the X eyes are independent, the variance is the sum of the variances
[03:16] the variance is the sum of the variances
[03:17] the variance is the sum of the variances and therefore we obtain n times the
[03:19] and therefore we obtain n times the variance of each one of them
[03:22] variance of each one of them and after we simplify, this leaves us
[03:25] and after we simplify, this leaves us with sigma squared over n.
[03:29] with sigma squared over n. We're now in a position to apply the
[03:31] We're now in a position to apply the Chebyshev inequality.
[03:33] Chebyshev inequality. The Chebyshev inequality tells us that
[03:37] The Chebyshev inequality tells us that the distance of a random variable from
[03:39] the distance of a random variable from its mean being larger than a certain
[03:41] its mean being larger than a certain number has a probability that's bounded
[03:44] number has a probability that's bounded above by the variance of the random
[03:47] above by the variance of the random variable of interest
[03:50] variable of interest divided by the square of the number that
[03:53] divided by the square of the number that we have here. We have already calculated
[03:56] we have here. We have already calculated the variance
[03:58] the variance and so this quantity is sigma squared
[04:02] and so this quantity is sigma squared over n times epsilon squared.
[04:06] over n times epsilon squared. And now, if we consider epsilon as a
[04:09] And now, if we consider epsilon as a fixed number and let n go to infinity,
[04:13] fixed number and let n go to infinity, then what we obtain is a limiting value
[04:17] then what we obtain is a limiting value of zero.
[04:22] So, the probability of falling far from
[04:24] So, the probability of falling far from the mean
[04:25] the mean diminishes to zero as we draw more and
[04:29] diminishes to zero as we draw more and more samples. That's exactly what the
[04:31] more samples. That's exactly what the
[04:32] more samples. That's exactly what the weak law of large numbers tells us. If
[04:34] weak law of large numbers tells us. If we fix any particular epsilon which is a
[04:37] we fix any particular epsilon which is a positive constant, the probability that
[04:40] positive constant, the probability that the sample mean falls away from the true
[04:43] the sample mean falls away from the true mean by more than epsilon, that
[04:46] mean by more than epsilon, that probability becomes smaller and smaller
[04:49] probability becomes smaller and smaller and converges to zero as n goes to
[04:51] and converges to zero as n goes to infinity.
[04:53] infinity. Let us now interpret the weak law of
[04:56] Let us now interpret the weak law of large numbers.
[04:58] large numbers. As I already hinted, we have to think in
[05:01] As I already hinted, we have to think in terms of one long experiment and during
[05:05] terms of one long experiment and during that experiment we draw several
[05:07] that experiment we draw several independent random variables drawn from
[05:10] independent random variables drawn from the same distribution. One way of
[05:12] the same distribution. One way of thinking about those random variables is
[05:14] thinking about those random variables is that each one of them is equal to the
[05:16] that each one of them is equal to the mean, the true mean, plus some
[05:19] mean, the true mean, plus some measurement noise which is a term that
[05:23] measurement noise which is a term that has zero expected value and all of these
[05:26] has zero expected value and all of these noises are independent. So, we have a
[05:28] noises are independent. So, we have a collection of noisy measurements and
[05:31] collection of noisy measurements and then we take those measurements and form
[05:33] then we take those measurements and form the average of them.
[05:36] the average of them. What the weak law of large numbers tells
[05:38] What the weak law of large numbers tells us is that the sample mean is unlikely
[05:42] us is that the sample mean is unlikely to be far off from the true mean and by
[05:45] to be far off from the true mean and by far off we mean at least epsilon
[05:48] far off we mean at least epsilon distance away.
[05:51] distance away. So, the sample mean is in some ways a
[05:54] So, the sample mean is in some ways a good way of estimating the true mean. If
[05:57] good way of estimating the true mean. If n is large enough, then we have high
[06:01] n is large enough, then we have high confidence that the sample mean gives us
[06:04] confidence that the sample mean gives us a value that's close to the true mean.
[06:07] a value that's close to the true mean. As a special case, let us consider a
[06:09] As a special case, let us consider a probabilistic model in which we repeat
[06:11] probabilistic model in which we repeat independently many times the same
[06:14] independently many times the same experiment. There's a certain event A
[06:16] experiment. There's a certain event A associated with that experiment that has
[06:18] associated with that experiment that has a certain probability and each time that
[06:21] a certain probability and each time that we carry out the experiment, we use an
[06:23] we carry out the experiment, we use an indicator variable to indicate whether
[06:27] indicator variable to indicate whether the outcome was inside the event or
[06:30] the outcome was inside the event or outside the event. So, X I is one if A
[06:35] outside the event. So, X I is one if A occurs
[06:39] and it is zero otherwise.
[06:44] The expected value of the X eyes, the
[06:47] The expected value of the X eyes, the true mean in this case, is equal to the
[06:49] true mean in this case, is equal to the
[06:50] true mean in this case, is equal to the number P.
[06:53] In this particular example, the sample
[06:56] In this particular example, the sample mean
[06:57] mean just counts how many times the event A
[07:00] just counts how many times the event A occurred out of the n experiments that
[07:03] occurred out of the n experiments that we carried out. So, it's the frequency
[07:05] we carried out. So, it's the frequency with which the event A has occurred
[07:08] with which the event A has occurred and we call it the empirical frequency
[07:10] and we call it the empirical frequency of event A. What the weak law of large
[07:13] of event A. What the weak law of large numbers tells us is that the empirical
[07:16] numbers tells us is that the empirical frequency will be close to the
[07:19] frequency will be close to the probability of that event.
[07:22] probability of that event. In this sense, it reinforces or
[07:25] In this sense, it reinforces or justifies the interpretation of
[07:27] justifies the interpretation of probabilities as frequencies.
