---
video_id: L2KMttDm3aY
url: https://www.youtube.com/watch?v=L2KMttDm3aY
title: An Introduction to the Hypergeometric Distribution
channel: jbstatistics
duration: 15:34
language: en
unit: L05
status: OK
---

[00:02] Let's look at an introduction to the hypergeometric distribution,
[00:04] another important discrete probability distribution.
[00:10] I'm going to assume that you know the combinations formula,
[00:12] also known as the binomial coefficient, both its meaning and how to calculate it,
[00:16] because it's going to play a big role in the hypergeometric distribution.
[00:19] If you don't recognize this, you should look into it before watching this video.
[00:22] I'm also going to assume that you've previously been introduced to the binomial distribution,
[00:27] because I'm going to be comparing the binomial and hypergeometric distributions here.
[00:33] Let's look at an example to start.
[00:35] An urn contains 6 red balls and 14 yellow balls.
[00:38] (These types of urn and balls problems are classic hypergeometric problems.)
[00:42] Five balls are randomly drawn without replacement.
[00:45] What is the probability exactly 4 red balls are drawn?
[00:49] An important point to note here is that the sampling is done without replacement,
[00:53] and by that I mean once a ball is chosen we look at the color and
[00:56] set it aside and it cannot be chosen again.
[00:59] And that implies that the trials are not independent.
[01:02] Knowing what happens on one trial gives some information about the probabilities on other trials.
[01:07] Because the trials are not independent, the binomial distribution would not be appropriate here.
[01:13] Before we take a formal look at the hypergeometric distribution,
[01:17] let's calculate this probability by thinking through the underlying logic.
[01:22] If we are randomly selecting five balls,
[01:24] then any sample of five balls is equally likely.
[01:28] The probability of getting exactly four red balls
[01:30] is the number of samples that result in exactly four red balls and one yellow ball
[01:34] (since we're picking five balls and four must be red, one must be yellow),
[01:38] divided by the total number of possible samples of size 5.
[01:44] Recall that there were 6 red balls and 14 yellow balls, for 20 balls in total.
[01:48] The total number of possible samples then is 20 choose 5.
[01:55] This is the combinations formula, the number of ways of picking 5 balls from 20.
[02:00] In the numerator we need the number of ways of getting four red balls and one yellow ball.
[02:04] There are 6 red balls, and from those we must pick 4,
[02:10] and there are 14 yellow balls, and from those we must pick 1,
[02:15] and so 6 choose 4
[02:16] times 14 choose 1 over 20 choose 5.
[02:20] If we use our combinations formula properly here
[02:23] we'll see that this works out to 15 times 14 over 15,504.
[02:31] To 5 decimal places this is 0.01354.
[02:41] It's not appropriate to use the binomial distribution here.
[02:45] Since the sampling is done without replacement, the trials are not independent.
[02:49] The probability of getting a red ball will change from trial to trial
[02:52] depending on what happened in other draws.
[02:56] For example, on the first draw, since there are 6 red balls and 14 yellow
[03:00] the probability of getting a red ball on that first draw is 6 out of 20 or 0.3.
[03:07] But suppose the first draw is a red ball.
[03:09] Then on the second draw the probability of getting a red ball is now only 5 out of 19.
[03:16] There's 5 red balls left out of 19 total, and that's a little less than 0.3.
[03:21] And so the probability of success on any individual trial depends on what has happened on the other trials.
[03:27] The trials are not independent
[03:30] and independence is one of the necessary conditions for the binomial distribution to hold.
[03:36] Suppose instead that the sampling had been done with replacement,
[03:40] meaning that when a ball is chosen we look at the color and count it,
[03:43] but place it back in the urn so that it might be chosen again.
[03:46] The probability of getting a red ball on any given trial is simply 6 out of 20,
[03:52] regardless of what happened on the other trials.
[03:55] And since the trials would be independent here,
[03:58] the binomial distribution would be appropriate.
[04:00] I'm not going to go into the details, but this would be the appropriate method of
[04:03] calculating the probability using the binomial formula.
[04:06] (You can see my video on the binomial distribution for more information.)
[04:10] To 5 decimal places this works out to 0.02835.
[04:18] Compare that to the probability we found previously using the hypergeometric distribution,
[04:22] when the sampling was done without replacement.
[04:25] There we found a probability of 0.01354.
[04:29] The probability found from the binomial distribution with replacement
[04:33] is actually quite a bit different from that.
[04:35] So if we were to mistakenly use the binomial distribution in the without replacement case
[04:39] our calculated probability would be quite a bit off.
[04:45] In our hypergeometric distribution example we simply thought through the problem
[04:48] and came up with the probability using some logic.
[04:51] But now let's give a little more formal introduction to the hypergeometric distribution.
[04:56] Suppose we are randomly sampling n objects without replacement
[04:59] from a source that contains
[05:01] a successes and capital N - a failures.
[05:04] There are capital N objects altogether. There's only two types of objects:
[05:09] the successes, and there are a of those,
[05:13] and the failures, and there are N-a of those.
[05:17] And we're going to let the random variable X
[05:19] represent the number of successes in the sample.
[05:25] Then the random variable X has the hypergeometric distribution, with this probability mass function.
[05:31] The probability the random variable X takes on the value little x,
[05:35] which I'll sometimes write as p(x), is equal to this quantity.
[05:42] In order to get little x successes from the total number of successes a,
[05:46] we must pick x of them,
[05:48] and from the N-a failures we must choose n-x of those
[05:53] and the denominator is simply the total number of samples,
[05:56] the number of ways are picking little n objects from capital N objects total.
[06:03] What values can X take on here? What are the possible number of successes?
[06:08] Well, it's the number of successes, so can only take on whole number values.
[06:12] The minimum and maximum numbers are a little bit messy.
[06:15] The number of successes in the sample can't possibly
[06:18] take on a value bigger than the number of objects we are choosing,
[06:21] so it couldn't possibly be bigger than n,
[06:25] and it also can't take on a value bigger than the number of successes in the population,
[06:30] so the maximum value X can take on is going to be the minimum of a and n.
[06:37] As for the minimum, we know that the number of successes can't possibly be less than 0,
[06:42] but it also can't be less than this quantity.
[06:46] To make that a little easier to see I'm going to write this as little n - (N-a)
[06:55] and this is the number of objects we are sampling minus the total number of failures in the population.
[07:00] The number successes has to be at least that quantity.
[07:04] So the minimum value X can take on is the maximum of 0 and this quantity.
[07:12] The mean of a hypergeometric distribution is equal to
[07:15] n times the number of successes a over the total number of objects, capital N.
[07:23] In other words, n times the proportion of successes in the population.
[07:29] Note that this looks a little bit like np,
[07:31] which is the mean of a binomial random variable,
[07:34] and it's pretty much the same thing here.
[07:38] There's also a formula for the variance, but it's a little ugly and I'm going to leave it out here.
[07:42] If you need it you can easily look it up.
[07:47] Let's look at a different example. Suppose a large high school has
[07:51] 1100 female students and 900 male students for 2000 students in total.
[07:56] A random sample of 10 students is drawn and we want to find
[07:58] the probability that exactly seven of the selected students are female.
[08:03] Here, although it doesn't state it explicitly,
[08:05] it's implied that the sampling is done without replacement.
[08:08] If, say, your boss asked you to get a sample of 10 people
[08:12] and you come back with 2 people
[08:13] and tell your boss you sampled one of them 6 times and the other one 4 times,
[08:17] you'll likely be looking for another job in the very near future.
[08:21] If we let the random variable X represent the number of female students selected,
[08:25] then we need to find the probability that the random variable X takes on the value 7.
[08:31] Again, I strongly recommend in this type of problem that
[08:34] you don't try to put the values into the formula and you simply try to think it through logically.
[08:38] Most people find it easier to find the correct probabilities that way.
[08:43] Here the denominator is going to be the total number of possible samples,
[08:47] and we are picking 10 students from 2000,
[08:50] and so the denominator is going to be 2000 choose 10.
[08:56] The numerator is the number of ways of getting exactly 7 female students,
[09:00] and from those 1100 female students we must pick 7.
[09:05] But we're not done yet. In order to get exactly seven female students in a sample of 10,
[09:11] we must also pick 3 male students,
[09:14] so from the 900 male students we must choose 3.
[09:19] The probability of getting exactly 7 females
[09:22] is 1100 choose 7 times 900 choose 3
[09:27] divided by 2000 choose 10.
[09:30] Note that 1100 plus 900 is equal to 2000,
[09:35] and 7 plus 3 is equal to 10.
[09:38] This is not a coincidence, and it will work out like that if done properly,
[09:41] and so that can be a useful double check on your calculations.
[09:46] To 6 decimal places this works out to 0.166490.
[09:55] If you feel the need to use the formula for the probability mass function on the previous slide,
[10:00] then capital N represents the total number of objects,
[10:03] or here the total number of students, and we had 2000 students.
[10:09] Little n represents the number of objects that we're sampling and that is 10.
[10:14] a is the total number of successes in the population,
[10:18] and since we're counting up the number of females
[10:21] we're calling getting a female student a success,
[10:23] and the total number of female students is 1100.
[10:29] If we put all of these into the formula for the probability mass function from the previous slide
[10:33] we'd get what we have over here.
[10:35] It might be informative to try that once, but most people find it easier
[10:38] if we just think it through logically and not rely on the formula.
[10:45] What if we had ignored the fact that the sampling was done without replacement,
[10:48] and we used the binomial distribution instead?
[10:51] What if we simply said the probability of getting a female student on any given trial
[10:55] is simply the number a female students we had, 1100,
[10:58] over the total number of students,
[11:00] and we said that that was 0.55 on each trial,
[11:04] and we ignored the fact that that's changing from trial to trial.
[11:09] If we put this into the binomial formula we would see that this works out to 0.166478.
[11:18] But since the sampling was done without replacement, that is not the correct probability.
[11:24] Recall that when we used the hypergeometric distribution on the last page,
[11:26] we found that the correct probability was 0.166490.
[11:32] Wait a minute, these two probabilities are pretty close.
[11:37] The incorrect one calculated with the binomial distribution
[11:39] is pretty darn close to the correct probability for this example.
[11:47] And that leads us to this point:
[11:48] the binomial distribution can sometimes be used to provide a reasonable approximation to the hypergeometric distribution.
[11:55] In most cases it will provide a reasonable approximation
[11:58] if we're not sampling a very large proportion of the population.
[12:01] And as a very rough guideline if we are not sampling more than 5% of the population,
[12:06] the binomial distribution would provide a reasonable approximation.
[12:11] Why would we want to use the binomial distribution as an approximation?
[12:14] Why wouldn't we simply use the hypergeometric distribution if it's the appropriate distribution?
[12:19] Well it turns out that in some cases the binomial distribution is easier to work with.
[12:23] In some probability calculations and statistical inference scenarios,
[12:27] the true underlying reality might imply a hypergeometric distribution,
[12:32] but the binomial distribution might provide a very good approximation,
[12:35] and might be much easier to work with.
[12:39] If we look back at this example we were sampling only 10 people out of 2000 total
[12:45] which is 0.5%.
[12:48] The guideline tells us that the binomial distribution would provide a reasonable approximation here.
[12:53] Why is this? Here 55% of the population is female,
[12:58] so the probability the first student selected is female is 0.55.
[13:03] But as students are selected
[13:05] the probability of selecting a female student is going to change a little bit,
[13:08] depending on what students were selected before.
[13:11] But since we're only sampling a small proportion of the population,
[13:14] the probability is not going to change very much.
[13:17] For example, suppose the first three students selected were female,
[13:21] the probability the next student selected is female is 1097, the number of remaining female students,
[13:28] over 1997, the total number of students remaining.
[13:32] This is a little bit less than 0.55, but it's still pretty close.
[13:37] So this probability changes only a little bit and the binomial distribution,
[13:41] which assumes a constant probability of success
[13:44] regardless of what happens on the other trials,
[13:46] provides a very reasonable approximation in this situation.
[13:52] One last thing. These methods can be extended to more than two groups,
[13:57] and let's take a quick look at that.
[14:00] Suppose that in the US a business employs
[14:02] 12 Democrats, 24 Republicans, and 8 independents.
[14:06] If a random sample of 6 employees is drawn,
[14:09] and suppose without replacement again,
[14:12] what is the probability there are 3 Democrats,
[14:14] 2 Republicans, and 1 independent in the sample?
[14:18] If we didn't rely on the formula in the earlier examples,
[14:20] and we understood the underlying logic,
[14:22] we can extend those methods to this type of situation,
[14:26] where there are three or more groups instead of just two.
[14:31] Here there are 12+24+8 people, or 44 altogether.
[14:38] So when we're calculating our probability, the total number of possible samples,
[14:43] which we put in the denominator
[14:45] is going to be 44 choose 6,
[14:48] because we're picking 6 people from 44.
[14:51] In the numerator we need the number of ways of getting 3 Democrats, 2 Republicans, and 1 independent.
[14:57] From the 12 Democrats we must pick 3,
[15:02] and from the 24 Republicans we must pick 2,
[15:06] and from the 8 independents we must pick 1.
[15:10] And all of this works out to 0.0688.
[15:18] So the methods the hypergeometric distribution can be extended to more than two types of object.
[15:23] This is sometimes called the multivariate hypergeometric,
[15:26] and this example is simply a very quick introduction to that.
