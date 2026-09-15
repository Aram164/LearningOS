---
video_id: H3EjCKtlVog
url: https://www.youtube.com/watch?v=H3EjCKtlVog
title: Gaussian Naive Bayes, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 9:26
language: en
unit: L14
status: OK
---

[00:03] StatQuest Hello, I'm Josh Starmer and welcome to
[00:07] Hello, I'm Josh Starmer and welcome to StatQuest. Today, we're going to talk
[00:10] StatQuest. Today, we're going to talk about Gaussian Naive Bayes and it's
[00:13] about Gaussian Naive Bayes and it's going to be clearly explained.
[00:16] going to be clearly explained. Note, this StatQuest assumes that you
[00:19] Note, this StatQuest assumes that you are already familiar with the main ideas
[00:21] are already familiar with the main ideas behind Multinomial Naive Bayes. If not,
[00:25] behind Multinomial Naive Bayes. If not, check out the quest. The link is in the
[00:27] check out the quest. The link is in the description below.
[00:29] description below. This StatQuest also assumes that you are
[00:32] This StatQuest also assumes that you are familiar with the log function,
[00:34] familiar with the log function, the normal or Gaussian distribution,
[00:37] the normal or Gaussian distribution, and the difference between probability
[00:40] and the difference between probability and likelihood. If not, check out the
[00:42] and likelihood. If not, check out the quests. The links are in the description
[00:45] quests. The links are in the description below.
[00:46] below. Imagine we wanted to predict if someone
[00:49] Imagine we wanted to predict if someone would love the 1990 movie Troll 2 or
[00:52] would love the 1990 movie Troll 2 or not.
[00:54] not. So, we collected data from people that
[00:56] So, we collected data from people that love Troll 2
[00:58] love Troll 2 and from people that do not love Troll
[01:01] and from people that do not love Troll 2.
[01:03] 2. We measured the amount of popcorn they
[01:05] We measured the amount of popcorn they ate each day,
[01:07] ate each day, how much soda pop they drank,
[01:10] how much soda pop they drank, and how much candy they ate.
[01:14] and how much candy they ate. The mean for popcorn for the people who
[01:16] The mean for popcorn for the people who love Troll 2 is 24.
[01:20] love Troll 2 is 24. And the standard deviation is four.
[01:23] And the standard deviation is four. And a Gaussian or normal distribution
[01:26] And a Gaussian or normal distribution with mean equals 24 and standard
[01:28] with mean equals 24 and standard deviation equals four looks like this.
[01:32] deviation equals four looks like this. Likewise, the average amount of popcorn
[01:35] Likewise, the average amount of popcorn for people who do not love Troll 2 is
[01:38] for people who do not love Troll 2 is four.
[01:39] four. And the standard deviation is two.
[01:43] And the standard deviation is two. And that corresponds to this Gaussian or
[01:46] And that corresponds to this Gaussian or normal distribution.
[01:48] normal distribution. Now, we calculate the mean and standard
[01:51] Now, we calculate the mean and standard deviation for soda pop for people that
[01:53] deviation for soda pop for people that love Troll 2
[01:55] love Troll 2 and draw the corresponding Gaussian
[01:58] and draw the corresponding Gaussian distribution.
[02:00] distribution. Then we do the same thing for the people
[02:02] Then we do the same thing for the people that do not love Troll 2.
[02:05] that do not love Troll 2. Lastly, we draw the Gaussian
[02:07] Lastly, we draw the Gaussian distributions for candy.
[02:11] distributions for candy. Gaussian naive Bayes is named after the
[02:13] Gaussian naive Bayes is named after the Gaussian distributions that represent
[02:16] Gaussian distributions that represent the data in the training data set.
[02:19] the data in the training data set. Now someone new shows up
[02:22] Now someone new shows up and says they eat 20 g of pop corn
[02:26] and says they eat 20 g of pop corn and drink 500 ml of soda pop
[02:30] and drink 500 ml of soda pop and eat 25 g of candy every day.
[02:35] and eat 25 g of candy every day. Let's use Gaussian naive Bayes to decide
[02:38] Let's use Gaussian naive Bayes to decide if they love Troll 2 or not.
[02:42] if they love Troll 2 or not. The first thing we do is make an initial
[02:44] The first thing we do is make an initial guess that they love Troll 2.
[02:48] guess that they love Troll 2. This guess can be any probability that
[02:50] This guess can be any probability that we want, but a common guess is estimated
[02:53] we want, but a common guess is estimated from the training data.
[02:55] from the training data. For example, since eight of the 16
[02:58] For example, since eight of the 16 people in the training data loved Troll
[03:00] people in the training data loved Troll 2, the initial guess will be 0.5.
[03:05] 2, the initial guess will be 0.5. So we'll put that up here so we don't
[03:07] So we'll put that up here so we don't forget.
[03:08] forget. Likewise, the initial guess for does not
[03:11] Likewise, the initial guess for does not love Troll 2 is 0.5.
[03:15] love Troll 2 is 0.5. So let's put that here so we don't
[03:17] So let's put that here so we don't forget.
[03:19] forget. Oh no, it's the dreaded terminology
[03:22] Oh no, it's the dreaded terminology alert.
[03:23] alert. The initial guesses are called prior
[03:26] The initial guesses are called prior probabilities.
[03:28] probabilities. Now, the score for loves Troll 2 is
[03:33] Now, the score for loves Troll 2 is the initial guess that the person loves
[03:35] the initial guess that the person loves Troll 2
[03:37] Troll 2 times the likelihood that they eat 10 g
[03:40] times the likelihood that they eat 10 g of popcorn given that they love Troll 2.
[03:44] of popcorn given that they love Troll 2. Note, the likelihood is the Y axis
[03:47] Note, the likelihood is the Y axis coordinate on the curve that corresponds
[03:49] coordinate on the curve that corresponds to the X axis coordinate.
[03:52] to the X axis coordinate. And we multiply that by the likelihood
[03:55] And we multiply that by the likelihood that they drink 500 ml of soda pop given
[03:58] that they drink 500 ml of soda pop given that they love Troll 2
[04:01] that they love Troll 2 times the likelihood that they eat 25 g
[04:04] times the likelihood that they eat 25 g of candy given that they love Troll 2.
[04:08] of candy given that they love Troll 2. The initial guess that someone loves
[04:10] The initial guess that someone loves Troll 2 is 0.5.
[04:13] Troll 2 is 0.5. The likelihood for popcorn is 0.06.
[04:18] The likelihood for popcorn is 0.06. The likelihood for soda pop is 0.004.
[04:24] And the likelihood for candy is
[04:27] And the likelihood for candy is a really, really small number.
[04:30] a really, really small number. Note, when we get really, really small
[04:33] Note, when we get really, really small numbers, it's a good idea to take the
[04:35] numbers, it's a good idea to take the log of everything to prevent something
[04:37] log of everything to prevent something called underflow.
[04:40] called underflow. The general idea of underflow is
[04:44] The general idea of underflow is every computer has a limit to how close
[04:46] every computer has a limit to how close a number can get to zero before it can
[04:49] a number can get to zero before it can no longer accurately keep track of that
[04:51] no longer accurately keep track of that number.
[04:53] number. When a number gets smaller than that
[04:55] When a number gets smaller than that limit, we run into underflow problems
[04:58] limit, we run into underflow problems and errors occur.
[05:00] and errors occur. So, we use the log function to avoid
[05:03] So, we use the log function to avoid underflow.
[05:05] underflow. Note, any log will do, but the natural
[05:08] Note, any log will do, but the natural log or log base e is the most commonly
[05:11] log or log base e is the most commonly used log in statistics and machine
[05:13] used log in statistics and machine learning.
[05:15] learning. So, we take the log of everything.
[05:19] So, we take the log of everything. And the log turns the multiplication
[05:22] And the log turns the multiplication into the sum of the individual logs.
[05:26] into the sum of the individual logs. The log base e of 0.5 is
[05:30] The log base e of 0.5 is -0.69.
[05:34] The log of 0.06 is -2.8.
[05:40] is -2.8. The log of 0.004
[05:42] The log of 0.004 is -5.5.
[05:46] And the log of this really, really small
[05:49] And the log of this really, really small number is -115.
[05:53] Now, we just add this up
[05:56] Now, we just add this up and we get -124.
[06:00] So, the log of the loves Troll 2 score
[06:03] So, the log of the loves Troll 2 score is -124.
[06:06] is -124. Bam!
[06:09] Bam! Now, let's calculate the score for not
[06:11] Now, let's calculate the score for not loving Troll 2.
[06:13] loving Troll 2. We start with the initial guess that
[06:15] We start with the initial guess that someone does not love Troll 2.
[06:19] someone does not love Troll 2. times the likelihood that they eat 20 g
[06:21] times the likelihood that they eat 20 g of popcorn given that they do not love
[06:24] of popcorn given that they do not love Troll 2.
[06:26] Troll 2. times the likelihood that they drink 500
[06:28] times the likelihood that they drink 500 ml of soda pop.
[06:31] ml of soda pop. times the likelihood that they eat 25 g
[06:34] times the likelihood that they eat 25 g of candy.
[06:36] of candy. So, let's plug in the numbers. Beep,
[06:38] So, let's plug in the numbers. Beep, boop, beep, boop.
[06:41] boop, beep, boop. And take the log of everything.
[06:44] And take the log of everything. And that turns the multiplication
[06:46] And that turns the multiplication into the sum of logs.
[06:49] into the sum of logs. Now, we just do the math. Beep, boop,
[06:52] Now, we just do the math. Beep, boop, boop, boop.
[06:53] boop, boop. And we get -48.
[06:57] And we get -48. And since the score for does not love
[06:59] And since the score for does not love Troll 2 is greater than the score for
[07:01] Troll 2 is greater than the score for loves Troll 2,
[07:04] loves Troll 2, we will classify this person as someone
[07:06] we will classify this person as someone who does not love Troll 2.
[07:09] who does not love Troll 2. Double bam!
[07:12] Double bam! Note, when we look at the raw data, it
[07:15] Note, when we look at the raw data, it almost looks like we should have
[07:16] almost looks like we should have classified this person as someone who
[07:18] classified this person as someone who loves Troll 2.
[07:21] loves Troll 2. After all, they ate a lot more popcorn
[07:24] After all, they ate a lot more popcorn than the average person who doesn't love
[07:26] than the average person who doesn't love Troll 2.
[07:28] Troll 2. And they drank as much soda as the
[07:30] And they drank as much soda as the average person who loves Troll 2.
[07:34] average person who loves Troll 2. However, the big thing is that they ate
[07:36] However, the big thing is that they ate a lot more candy than the people who
[07:38] a lot more candy than the people who loved Troll 2.
[07:41] loved Troll 2. And the log of the likelihoods for candy
[07:43] And the log of the likelihoods for candy are way different.
[07:46] are way different. And this difference is what made us
[07:48] And this difference is what made us classify the new person as someone who
[07:50] classify the new person as someone who does not love Troll 2.
[07:53] does not love Troll 2. In other words, candy can have a much
[07:56] In other words, candy can have a much larger say in whether or not someone
[07:58] larger say in whether or not someone loves Troll 2 than popcorn and soda pop.
[08:02] loves Troll 2 than popcorn and soda pop. And this means we might only need candy
[08:05] And this means we might only need candy to make classifications.
[08:08] to make classifications. We can use cross validation to help us
[08:10] We can use cross validation to help us decide which things, popcorn, soda pop,
[08:14] decide which things, popcorn, soda pop, and or candy, help us make the best
[08:17] and or candy, help us make the best classifications.
[08:19] classifications. Shameless self-promotion.
[08:22] Shameless self-promotion. If you don't already know about cross
[08:23] If you don't already know about cross validation, check out the quest. The
[08:26] validation, check out the quest. The link is in the description below.
[08:29] link is in the description below. Triple bam!
[08:32] Triple bam! Oh, no! It's another shameless
[08:35] Oh, no! It's another shameless self-promotion.
[08:37] self-promotion. One awesome way to support StatQuest is
[08:40] One awesome way to support StatQuest is to purchase the Gaussian naive Bayes
[08:42] to purchase the Gaussian naive Bayes StatQuest study guide. It has everything
[08:45] StatQuest study guide. It has everything you need to study for an exam or job
[08:47] you need to study for an exam or job interview.
[08:48] interview. It's seven pages of total awesomeness.
[08:53] It's seven pages of total awesomeness. And while you're there, check out the
[08:55] And while you're there, check out the other StatQuest study guides. There's
[08:57] other StatQuest study guides. There's something for everyone.
[08:59] something for everyone. Hooray! We've made it to the end of
[09:02] Hooray! We've made it to the end of another exciting StatQuest. If you like
[09:04] another exciting StatQuest. If you like this StatQuest and want to see more,
[09:06] this StatQuest and want to see more, please subscribe. And if you want to
[09:08] please subscribe. And if you want to support StatQuest, consider contributing
[09:11] support StatQuest, consider contributing to my Patreon campaign, becoming a
[09:13] to my Patreon campaign, becoming a channel member, buying one or two of my
[09:15] channel member, buying one or two of my original songs or a t-shirt or a hoodie,
[09:18] original songs or a t-shirt or a hoodie, or just donate. The links are in the
[09:20] or just donate. The links are in the description below. All right. Until next
[09:23] description below. All right. Until next time, quest on.
