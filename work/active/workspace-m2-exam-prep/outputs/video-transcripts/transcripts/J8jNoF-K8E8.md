---
video_id: J8jNoF-K8E8
url: https://www.youtube.com/watch?v=J8jNoF-K8E8
title: The Binomial Distribution and Test, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 15:46
language: en
unit: L07
status: OK
---

[00:00] StatQuest is cool.
[00:04] StatQuest is cool. That's my opinion.
[00:08] That's my opinion. If you don't think so,
[00:11] If you don't think so, then your opinion is inversely
[00:13] then your opinion is inversely correlated with mine. StatQuest
[00:19] Hello and welcome to StatQuest. Today
[00:22] Hello and welcome to StatQuest. Today we're going to talk about the binomial
[00:23] we're going to talk about the binomial distribution and the binomial test and
[00:26] distribution and the binomial test and they're going to be clearly explained.
[00:29] they're going to be clearly explained. Usually when people talk about the
[00:31] Usually when people talk about the binomial distribution, they talk about
[00:33] binomial distribution, they talk about flipping a coin.
[00:36] flipping a coin. A coin usually has heads
[00:38] A coin usually has heads and at least one tail.
[00:40] and at least one tail. For example, you can use the binomial
[00:43] For example, you can use the binomial distribution to find out the probability
[00:45] distribution to find out the probability of getting six heads in six tosses.
[00:49] of getting six heads in six tosses. But who really cares about flipping
[00:51] But who really cares about flipping coins?
[00:53] coins? What folks really want to know is
[00:55] What folks really want to know is whether or not people like orange Fanta
[00:58] whether or not people like orange Fanta more than grape Fanta.
[01:00] more than grape Fanta. Which flavor reigns supreme?
[01:04] Which flavor reigns supreme? Or are they both equally loved?
[01:07] Or are they both equally loved? To answer this question, we can ask a
[01:10] To answer this question, we can ask a bunch of people which flavor they
[01:12] bunch of people which flavor they prefer.
[01:14] prefer. If everybody but one person said they
[01:16] If everybody but one person said they liked orange Fanta more than grape
[01:18] liked orange Fanta more than grape Fanta, then it would be pretty obvious
[01:20] Fanta, then it would be pretty obvious what people liked most.
[01:23] what people liked most. But what if four people say they like
[01:25] But what if four people say they like orange Fanta and three people say they
[01:27] orange Fanta and three people say they like grape Fanta?
[01:30] like grape Fanta? Is that enough to be confident that most
[01:32] Is that enough to be confident that most people like orange Fanta?
[01:35] people like orange Fanta? Or could it be that people in general
[01:38] Or could it be that people in general don't have a preference and these
[01:40] don't have a preference and these results are just due to random chance
[01:42] results are just due to random chance and a small sample size?
[01:45] and a small sample size? Maybe if we surveyed another seven
[01:47] Maybe if we surveyed another seven people, we might only get three people
[01:49] people, we might only get three people who like orange Fanta and four people
[01:52] who like orange Fanta and four people who like grape Fanta.
[01:55] who like grape Fanta. To get to the bottom of this mystery, we
[01:57] To get to the bottom of this mystery, we need to get a sense of what to expect if
[02:00] need to get a sense of what to expect if there is no preference.
[02:03] there is no preference. Then we determine if our survey results
[02:05] Then we determine if our survey results fit those expectations.
[02:07] fit those expectations. If not, we can reject the idea that both
[02:10] If not, we can reject the idea that both Fantas are loved equally.
[02:13] Fantas are loved equally. The binomial distribution will tell us
[02:16] The binomial distribution will tell us what to expect if there is no
[02:17] what to expect if there is no preference.
[02:20] preference. To say the same thing using statistics
[02:22] To say the same thing using statistics lingo,
[02:23] lingo, we will use the binomial distribution,
[02:26] we will use the binomial distribution, aka this nasty looking thing,
[02:30] aka this nasty looking thing, to model what to expect when there is no
[02:33] to model what to expect when there is no preference.
[02:35] preference. Then we'll see how well this model fits
[02:37] Then we'll see how well this model fits the data.
[02:39] the data. If the model is a poor fit, we will
[02:41] If the model is a poor fit, we will reject the idea that both flavors are
[02:44] reject the idea that both flavors are loved equally.
[02:47] loved equally. So let's start with a super simple
[02:49] So let's start with a super simple example and assume that I asked three
[02:51] example and assume that I asked three people if they liked orange Fanta more
[02:54] people if they liked orange Fanta more than grape Fanta.
[02:57] than grape Fanta. The first person we asked said they
[02:59] The first person we asked said they preferred orange Fanta.
[03:02] preferred orange Fanta. The second person we asked also said
[03:04] The second person we asked also said they preferred orange Fanta.
[03:08] they preferred orange Fanta. And the third person we asked said they
[03:10] And the third person we asked said they preferred grape Fanta.
[03:13] preferred grape Fanta. If people really didn't prefer one
[03:15] If people really didn't prefer one flavor over the other,
[03:17] flavor over the other, then we will assume that there's a 50%
[03:19] then we will assume that there's a 50% chance they will pick orange and a 50%
[03:22] chance they will pick orange and a 50% chance they will pick grape.
[03:25] chance they will pick grape. We can then calculate the probability of
[03:28] We can then calculate the probability of the first two people randomly choosing
[03:30] the first two people randomly choosing orange and the third person randomly
[03:33] orange and the third person randomly choosing grape.
[03:35] choosing grape. Assuming that there is no real
[03:37] Assuming that there is no real preference, the probability of the first
[03:39] preference, the probability of the first person preferring orange Fanta is 0.5.
[03:45] person preferring orange Fanta is 0.5. And the probability of the first two
[03:47] And the probability of the first two people preferring orange Fanta is 0.5 *
[03:51] people preferring orange Fanta is 0.5 * 0.5, which equals 0.25.
[03:56] And the probability of the first two people preferring orange Fanta and the
[04:01] people preferring orange Fanta and the third person preferring grape is 0.5 *
[04:05] third person preferring grape is 0.5 * 0.5 * 0.5,
[04:08] 0.5 * 0.5, which equals 0.125.
[04:13] Note, 0.125
[04:16] Note, 0.125 is the probability of the first two
[04:18] is the probability of the first two people saying they prefer orange and the
[04:21] people saying they prefer orange and the third person saying they prefer grape.
[04:24] third person saying they prefer grape. It is not the probability that any two
[04:27] It is not the probability that any two out of three people would prefer orange.
[04:32] out of three people would prefer orange. Let me explain.
[04:34] Let me explain. It could have just as easily been that
[04:36] It could have just as easily been that the first person said they preferred
[04:38] the first person said they preferred grape.
[04:40] grape. In this case, the probability would
[04:42] In this case, the probability would still be 0.125,
[04:45] still be 0.125, but we'd multiply the numbers together
[04:47] but we'd multiply the numbers together in a different order.
[04:50] in a different order. Likewise, if the second person said they
[04:52] Likewise, if the second person said they preferred grape, we just multiply the
[04:54] preferred grape, we just multiply the numbers together in a different order.
[04:58] numbers together in a different order. So, all three of these combinations are
[05:00] So, all three of these combinations are equally likely.
[05:03] equally likely. And this means that the probability that
[05:05] And this means that the probability that any two out of three people prefer
[05:08] any two out of three people prefer orange Fanta is the sum of the three
[05:11] orange Fanta is the sum of the three possible orders.
[05:13] possible orders. So, we just add the three probabilities
[05:15] So, we just add the three probabilities together.
[05:18] together. And the probability that any two out of
[05:20] And the probability that any two out of three people would randomly say they
[05:22] three people would randomly say they prefer orange Fanta is 0.375.
[05:27] Alternatively, we could have done the
[05:30] Alternatively, we could have done the math using this nasty-looking formula.
[05:34] math using this nasty-looking formula. X is the number of people who preferred
[05:36] X is the number of people who preferred orange Fanta.
[05:38] orange Fanta. In this case, X equals 2.
[05:42] In this case, X equals 2. N is the total number of people we
[05:44] N is the total number of people we asked. In this case, n = 3.
[05:49] asked. In this case, n = 3. Note,
[05:50] Note, n - x, the total number of people we
[05:53] n - x, the total number of people we asked minus the number of people who
[05:55] asked minus the number of people who preferred orange Fanta, equals the
[05:58] preferred orange Fanta, equals the number of people who said they prefer
[06:00] number of people who said they prefer grape Fanta.
[06:03] grape Fanta. P is the probability that someone will
[06:05] P is the probability that someone will pick orange Fanta. In this case, p =
[06:09] pick orange Fanta. In this case, p = 0.5.
[06:12] 0.5. Note, the probability that someone might
[06:14] Note, the probability that someone might prefer grape Fanta is 1 - p.
[06:19] prefer grape Fanta is 1 - p. Together, this says the probability of
[06:22] Together, this says the probability of x, the number of people who say they
[06:25] x, the number of people who say they prefer orange Fanta, given n, the number
[06:28] prefer orange Fanta, given n, the number of people we asked, and p, the
[06:31] of people we asked, and p, the probability of picking orange Fanta,
[06:34] probability of picking orange Fanta, equals this nasty looking thing.
[06:38] equals this nasty looking thing. Ooh, it's got factorials.
[06:43] Ooh, it's got factorials. Don't freak out.
[06:44] Don't freak out. It looks fancy, but it just boils down
[06:47] It looks fancy, but it just boils down to the number of different ways two of
[06:49] to the number of different ways two of three people could say they prefer
[06:51] three people could say they prefer orange Fanta.
[06:54] orange Fanta. When we did everything by hand, we saw
[06:57] When we did everything by hand, we saw that there were three ways for two of
[06:59] that there were three ways for two of three people to say they prefer orange
[07:02] three people to say they prefer orange Fanta.
[07:04] Fanta. And if we plug in n = 3 and x = 2,
[07:10] And if we plug in n = 3 and x = 2, and then just do the math,
[07:16] we get three. Three ways that two out of three people
[07:21] Three ways that two out of three people could prefer orange Fanta,
[07:23] could prefer orange Fanta, just like when we did it by hand.
[07:26] just like when we did it by hand. So, this fancy thing is really no big
[07:29] So, this fancy thing is really no big deal.
[07:31] deal. The next part of the formula, p to the
[07:33] The next part of the formula, p to the x, corresponds to the probability that
[07:36] x, corresponds to the probability that orange Fanta was chosen two of the three
[07:39] orange Fanta was chosen two of the three times.
[07:41] times. In other words, P to the X just
[07:44] In other words, P to the X just consolidates 0.5 * 0.5
[07:48] consolidates 0.5 * 0.5 into 0.5 squared.
[07:52] The last part of the equation corresponds to the probability that
[07:56] corresponds to the probability that someone preferred grape Fanta.
[07:59] someone preferred grape Fanta. Remember that 1 - P is the probability
[08:03] Remember that 1 - P is the probability that someone prefers grape Fanta.
[08:07] that someone prefers grape Fanta. And N - X is the number of people that
[08:09] And N - X is the number of people that said that they preferred grape Fanta.
[08:13] said that they preferred grape Fanta. If we plug in N = 3, X = 2, and P = 0.5,
[08:20] If we plug in N = 3, X = 2, and P = 0.5, and then do the math,
[08:23] and then do the math, we get 0.5.
[08:26] we get 0.5. So, this term corresponds to the one
[08:28] So, this term corresponds to the one person who liked grape Fanta.
[08:32] person who liked grape Fanta. Thus, these two parts of the equation
[08:35] Thus, these two parts of the equation correspond to 0.5 * 0.5 * 0.5.
[08:42] And the nasty part just multiplies it by three.
[08:47] three. Now, we can put all the parts together
[08:50] Now, we can put all the parts together and plug in X = 2, the number of people
[08:54] and plug in X = 2, the number of people that preferred orange Fanta,
[08:56] that preferred orange Fanta, N = 3, the number of people we asked,
[08:59] N = 3, the number of people we asked, and P = 0.5, the probability someone
[09:03] and P = 0.5, the probability someone would randomly pick orange Fanta.
[09:06] would randomly pick orange Fanta. And we get the same probability that two
[09:09] And we get the same probability that two out of three people would randomly
[09:10] out of three people would randomly prefer orange Fanta that we got when we
[09:13] prefer orange Fanta that we got when we did everything by hand, 0.375.
[09:19] In other words, the binomial distribution tells us that the
[09:22] distribution tells us that the probability that two of three people
[09:25] probability that two of three people will prefer orange Fanta due to random
[09:27] will prefer orange Fanta due to random chance is 0.375.
[09:32] Bam!
[09:35] Bam! Calculating the probability of three of
[09:37] Calculating the probability of three of three people saying they prefer orange
[09:39] three people saying they prefer orange Fanta by hand is pretty easy since
[09:42] Fanta by hand is pretty easy since there's only one combination.
[09:45] there's only one combination. But we can just as easily use the fancy
[09:48] But we can just as easily use the fancy formula by plugging in x equals three.
[09:51] formula by plugging in x equals three. And then we just do the math.
[09:54] And then we just do the math. This term equals one since we are
[09:57] This term equals one since we are dividing three factorial by three
[09:59] dividing three factorial by three factorial.
[10:01] factorial. And this term is also equal one because
[10:05] And this term is also equal one because anything raised to the zero power equals
[10:07] anything raised to the zero power equals one.
[10:09] one. And then we just keep doing the math.
[10:15] And this means that the probability of three of three people randomly
[10:19] three of three people randomly preferring orange Fanta is 0.125.
[10:25] Which is exactly what we got when we did the calculations by hand.
[10:30] the calculations by hand. Now that we've seen that we can
[10:32] Now that we've seen that we can calculate probabilities with the
[10:34] calculate probabilities with the binomial distribution, let's go back to
[10:36] binomial distribution, let's go back to our original question.
[10:38] our original question. If four people say they like orange
[10:40] If four people say they like orange Fanta and three people say they like
[10:42] Fanta and three people say they like grape Fanta, can we conclude that people
[10:45] grape Fanta, can we conclude that people in general prefer orange Fanta?
[10:49] in general prefer orange Fanta? Now we plug in x equals four, the number
[10:52] Now we plug in x equals four, the number of people that preferred orange Fanta, n
[10:55] of people that preferred orange Fanta, n equals seven, the number of people we
[10:58] equals seven, the number of people we asked, and p equals 0.5,
[11:01] asked, and p equals 0.5, the probability someone would randomly
[11:03] the probability someone would randomly pick orange Fanta.
[11:06] pick orange Fanta. And then just do the math.
[11:12] And we get 0.273,
[11:15] And we get 0.273, the probability that four of seven
[11:17] the probability that four of seven people would randomly prefer orange
[11:19] people would randomly prefer orange Fanta.
[11:21] Fanta. Double bam!
[11:25] Double bam! When you use a binomial distribution to
[11:27] When you use a binomial distribution to calculate a p value, it's called a
[11:30] calculate a p value, it's called a binomial test.
[11:32] binomial test. So what's the P value for four out of
[11:35] So what's the P value for four out of seven people preferring orange Fanta?
[11:39] seven people preferring orange Fanta? The P value is the probability of the
[11:42] The P value is the probability of the observed data
[11:43] observed data four of seven people prefer orange Fanta
[11:46] four of seven people prefer orange Fanta plus the probabilities of all other
[11:49] plus the probabilities of all other possibilities that are equally likely or
[11:52] possibilities that are equally likely or rarer.
[11:54] rarer. This means we need to calculate these
[11:56] This means we need to calculate these probabilities.
[11:59] probabilities. These are the observed results of our
[12:00] These are the observed results of our poll
[12:03] poll and these are rare possibilities.
[12:06] and these are rare possibilities. And we also need to calculate the
[12:08] And we also need to calculate the probabilities of these combinations.
[12:12] probabilities of these combinations. These two possibilities
[12:14] These two possibilities four versus three and three versus four
[12:18] four versus three and three versus four are equally rare.
[12:21] are equally rare. If you don't believe me, plug in the
[12:23] If you don't believe me, plug in the numbers and see.
[12:26] numbers and see. The remaining possibilities are rarer.
[12:30] In other words, by including possibilities when grape Fanta is
[12:34] possibilities when grape Fanta is preferred equally or more often, we are
[12:37] preferred equally or more often, we are calculating a two-sided P value.
[12:41] calculating a two-sided P value. If this is blowing your mind, don't
[12:43] If this is blowing your mind, don't freak out. Just watch the StatQuest on P
[12:47] freak out. Just watch the StatQuest on P values clearly explained and one and
[12:50] values clearly explained and one and two-sided P values. The links are in the
[12:52] two-sided P values. The links are in the description below.
[12:55] description below. We've already calculated the probability
[12:58] We've already calculated the probability that four out of seven people prefer
[13:00] that four out of seven people prefer orange Fanta.
[13:01] orange Fanta. It's 0.273.
[13:05] For this, we just set X to five and plug
[13:08] For this, we just set X to five and plug and chug.
[13:10] and chug. And we get 0.164.
[13:14] Then we get 0.055.
[13:18] And then we get 0.008.
[13:23] Adding the probabilities together gives us 0.5.
[13:27] us 0.5. The probability that orange Fanta is
[13:29] The probability that orange Fanta is preferred.
[13:32] preferred. Now we just plug and chug the numbers
[13:34] Now we just plug and chug the numbers for when grape Fanta is preferred.
[13:40] Adding the probabilities together gives us 0.5,
[13:44] us 0.5, the probability that orange Fanta is not
[13:47] the probability that orange Fanta is not preferred.
[13:49] preferred. The sum of the probabilities of all
[13:51] The sum of the probabilities of all combinations of events that have an
[13:53] combinations of events that have an equal probability or are rarer equals
[13:56] equal probability or are rarer equals 0.5 + 0.5, which equals 1.
[14:02] 0.5 + 0.5, which equals 1. Which means the P value for four out of
[14:05] Which means the P value for four out of seven people saying they prefer orange
[14:07] seven people saying they prefer orange Fanta is 1.
[14:10] Fanta is 1. Which means that the model, the binomial
[14:13] Which means that the model, the binomial distribution with P equals 0.5,
[14:16] distribution with P equals 0.5, i.e. orange Fanta and grape Fanta are
[14:19] i.e. orange Fanta and grape Fanta are both equally loved, is a good fit for
[14:22] both equally loved, is a good fit for the observed data.
[14:25] the observed data. Thus, we conclude that, given the sample
[14:28] Thus, we conclude that, given the sample size seven, we cannot rule out the
[14:31] size seven, we cannot rule out the possibility that both orange Fanta and
[14:34] possibility that both orange Fanta and grape Fanta are equally loved.
[14:38] grape Fanta are equally loved. Think about that the next time you watch
[14:40] Think about that the next time you watch the World Series of Baseball.
[14:44] the World Series of Baseball. Triple bam.
[14:47] One last thing before we're done.
[14:51] One last thing before we're done. The binomial distribution only works
[14:53] The binomial distribution only works when the probability that someone likes
[14:55] when the probability that someone likes orange Fanta does not change if someone
[14:58] orange Fanta does not change if someone else already said they liked orange
[15:00] else already said they liked orange Fanta.
[15:02] Fanta. In other words, if we ask a bunch of
[15:04] In other words, if we ask a bunch of people if they like orange Fanta and
[15:07] people if they like orange Fanta and they all say, "Yes."
[15:09] they all say, "Yes." Then that should not affect the
[15:11] Then that should not affect the probability that the next person also
[15:13] probability that the next person also likes orange Fanta.
[15:16] likes orange Fanta. Hooray! We've made it to the end of
[15:19] Hooray! We've made it to the end of another exciting StatQuest.
[15:21] another exciting StatQuest. If you like this StatQuest and want to
[15:23] If you like this StatQuest and want to see more of them, please subscribe. And
[15:25] see more of them, please subscribe. And if you want to support Stat Quest, well,
[15:28] if you want to support Stat Quest, well, please click the like button below and
[15:30] please click the like button below and consider buying one or two of my
[15:32] consider buying one or two of my original songs. All right, until next
[15:35] original songs. All right, until next time, quest on.
