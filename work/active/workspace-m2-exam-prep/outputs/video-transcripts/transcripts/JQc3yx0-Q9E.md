---
video_id: JQc3yx0-Q9E
url: https://www.youtube.com/watch?v=JQc3yx0-Q9E
title: How to calculate p-values
channel: StatQuest with Josh Starmer
duration: 25:15
language: en
unit: L10
status: OK
---

[00:00] Calculating P values is kind of fun and
[00:03] Calculating P values is kind of fun and not just when you're done. StatQuest
[00:08] not just when you're done. StatQuest Hello, I'm Josh Starmer and welcome to
[00:11] Hello, I'm Josh Starmer and welcome to StatQuest. Today we're going to talk
[00:13] StatQuest. Today we're going to talk about how to calculate P values.
[00:16] about how to calculate P values. Note, this StatQuest assumes that you
[00:19] Note, this StatQuest assumes that you are already familiar with what P values
[00:21] are already familiar with what P values are and how to interpret them. If not,
[00:25] are and how to interpret them. If not, check out the quest.
[00:27] check out the quest. Also note, before we get started, I want
[00:30] Also note, before we get started, I want to mention that there are two types of P
[00:32] to mention that there are two types of P values.
[00:34] values. One-sided and two-sided.
[00:37] One-sided and two-sided. Two-sided P values are the most common
[00:40] Two-sided P values are the most common and this quest focuses on calculating
[00:43] and this quest focuses on calculating them.
[00:44] them. In contrast, one-sided P values are
[00:47] In contrast, one-sided P values are rarely used and to be honest,
[00:50] rarely used and to be honest, potentially dangerous. I won't mention
[00:53] potentially dangerous. I won't mention them again until the very end when I
[00:55] them again until the very end when I give an example of why they should be
[00:57] give an example of why they should be avoided.
[00:58] avoided. With that said, let's imagine I had a
[01:01] With that said, let's imagine I had a coin.
[01:03] coin. And I flipped it once and got heads.
[01:06] And I flipped it once and got heads. Then I flipped it again and got heads a
[01:09] Then I flipped it again and got heads a second time.
[01:11] second time. Now, at this point, I might be tempted
[01:14] Now, at this point, I might be tempted to think, "Wow, my coin is super special
[01:17] to think, "Wow, my coin is super special because it landed on heads twice in a
[01:19] because it landed on heads twice in a row."
[01:21] row." This is a hypothesis.
[01:25] This is a hypothesis. However, in statistics lingo, the
[01:28] However, in statistics lingo, the hypothesis is even though I got two
[01:31] hypothesis is even though I got two heads in a row, my coin is no different
[01:34] heads in a row, my coin is no different from a normal coin.
[01:37] from a normal coin. Note, although we want to know if our
[01:39] Note, although we want to know if our coin is special,
[01:41] coin is special, the statistics lingo version says the
[01:44] the statistics lingo version says the opposite, that our coin is the same as a
[01:47] opposite, that our coin is the same as a normal coin.
[01:49] normal coin. Statisticians call this the null
[01:51] Statisticians call this the null hypothesis and a small P value will tell
[01:54] hypothesis and a small P value will tell us to reject it.
[01:57] us to reject it. And if we reject this null hypothesis,
[02:00] And if we reject this null hypothesis, we will know that our coin is special.
[02:03] we will know that our coin is special. So, let's test this hypothesis by
[02:05] So, let's test this hypothesis by calculating a P value.
[02:08] calculating a P value. P values are determined by adding up
[02:10] P values are determined by adding up probabilities. So, let's start by
[02:12] probabilities. So, let's start by figuring out the probability of getting
[02:15] figuring out the probability of getting two heads in a row.
[02:18] two heads in a row. When we flip a normal everyday coin,
[02:21] When we flip a normal everyday coin, there's a 50% chance we'll get heads
[02:24] there's a 50% chance we'll get heads and a 50% chance we'll get tails.
[02:28] and a 50% chance we'll get tails. Now, if we got heads on the first flip
[02:32] Now, if we got heads on the first flip and flip the coin a second time,
[02:35] and flip the coin a second time, then, just like before, there's a 50%
[02:38] then, just like before, there's a 50% chance we'll get heads and a 50% chance
[02:41] chance we'll get heads and a 50% chance we'll get tails.
[02:43] we'll get tails. Likewise, if we got tails on the first
[02:46] Likewise, if we got tails on the first flip
[02:47] flip and flip the coin again,
[02:50] and flip the coin again, then, just like before, there's a 50%
[02:53] then, just like before, there's a 50% chance we'll get heads and a 50% chance
[02:56] chance we'll get heads and a 50% chance we'll get tails.
[02:58] we'll get tails. Ultimately, these are the four possible
[03:01] Ultimately, these are the four possible outcomes after flipping a coin two
[03:03] outcomes after flipping a coin two times.
[03:05] times. Because each outcome is equally
[03:07] Because each outcome is equally probable, we can calculate the
[03:09] probable, we can calculate the probability of getting two heads with
[03:11] probability of getting two heads with the following formula.
[03:13] the following formula. The number of times we got two heads
[03:16] The number of times we got two heads divided by the total number of outcomes.
[03:20] divided by the total number of outcomes. In this case, we only got two heads one
[03:23] In this case, we only got two heads one time.
[03:24] time. So, we put a one in the numerator.
[03:28] So, we put a one in the numerator. And since there were four possible
[03:30] And since there were four possible outcomes,
[03:31] outcomes, we put a four in the denominator.
[03:35] we put a four in the denominator. Thus, the probability of getting two
[03:37] Thus, the probability of getting two heads is 0.25.
[03:41] Likewise, the probability of getting two
[03:44] Likewise, the probability of getting two tails is
[03:46] tails is 0.25.
[03:49] Finally, the probability of getting one
[03:52] Finally, the probability of getting one heads and one tails regardless of the
[03:55] heads and one tails regardless of the order is 0.5.
[03:59] Now, you may be wondering why we don't
[04:02] Now, you may be wondering why we don't care about the order of the heads and
[04:04] care about the order of the heads and tails and treat these outcomes as the
[04:06] tails and treat these outcomes as the same.
[04:08] same. In this case, the order doesn't matter
[04:10] In this case, the order doesn't matter because getting a heads on the first
[04:12] because getting a heads on the first flip
[04:14] flip doesn't change the probabilities of
[04:16] doesn't change the probabilities of getting heads or tails on the second
[04:18] getting heads or tails on the second flip.
[04:20] flip. Likewise, getting tails on the first
[04:22] Likewise, getting tails on the first flip
[04:23] flip doesn't change the probabilities of
[04:25] doesn't change the probabilities of getting heads or tails on the second
[04:28] getting heads or tails on the second flip.
[04:29] flip. Because order does not affect the
[04:31] Because order does not affect the probabilities of getting heads and
[04:33] probabilities of getting heads and tails, we treat these outcomes as the
[04:35] tails, we treat these outcomes as the same.
[04:37] same. Now, let's move the outcomes over to the
[04:39] Now, let's move the outcomes over to the left
[04:41] left and list the probability of each outcome
[04:45] and list the probability of each outcome and calculate the P value for getting
[04:47] and calculate the P value for getting two heads.
[04:49] two heads. A P value is composed of three parts.
[04:54] A P value is composed of three parts. The first part is the probability random
[04:57] The first part is the probability random chance would result in the observation.
[05:00] chance would result in the observation. In this case, the first part is just the
[05:03] In this case, the first part is just the probability that a normal coin would
[05:05] probability that a normal coin would give us two heads, which is 0.25.
[05:10] The second part is the probability of
[05:13] The second part is the probability of observing something else that is equally
[05:15] observing something else that is equally rare.
[05:17] rare. In this case, getting two tails is as
[05:20] In this case, getting two tails is as rare as two heads, so we add 0.25.
[05:26] The third part is the probability of observing something rarer or more
[05:30] observing something rarer or more extreme.
[05:32] extreme. In this case, the third part is zero
[05:35] In this case, the third part is zero because no other outcomes are rarer than
[05:37] because no other outcomes are rarer than two heads or two tails.
[05:41] two heads or two tails. Now, we just add everything together.
[05:44] Now, we just add everything together. And the P value for getting two heads
[05:46] And the P value for getting two heads equals 0.5.
[05:50] equals 0.5. Now, remember, the reason we calculated
[05:52] Now, remember, the reason we calculated the P value was to test this hypothesis.
[05:56] the P value was to test this hypothesis. Even though I got two heads in a row, my
[05:59] Even though I got two heads in a row, my coin is no different from a normal coin.
[06:03] coin is no different from a normal coin. Typically, we only reject a hypothesis
[06:06] Typically, we only reject a hypothesis if the P value is less than 0.05.
[06:11] And since 0.5 is greater than 0.05,
[06:16] And since 0.5 is greater than 0.05, we fail to reject the hypothesis.
[06:19] we fail to reject the hypothesis. In other words, the data, getting two
[06:22] In other words, the data, getting two heads in a row, failed to convince us
[06:25] heads in a row, failed to convince us that our coin is special.
[06:28] that our coin is special. Note, the probability of getting two
[06:31] Note, the probability of getting two heads, 0.25,
[06:33] heads, 0.25, is different from the P value for
[06:35] is different from the P value for getting two heads, 0.5.
[06:39] getting two heads, 0.5. This is because the P value is the sum
[06:42] This is because the P value is the sum of three parts.
[06:44] of three parts. The first part is the probability random
[06:47] The first part is the probability random chance would result in the observation.
[06:50] chance would result in the observation. The second part is the probability of
[06:52] The second part is the probability of observing something else that is equally
[06:55] observing something else that is equally rare.
[06:56] rare. And the third part is the probability of
[06:59] And the third part is the probability of observing something rarer or more
[07:01] observing something rarer or more extreme.
[07:03] extreme. Now, the question is, why do we care
[07:06] Now, the question is, why do we care about things that are equally rare or
[07:08] about things that are equally rare or more extreme?
[07:10] more extreme? In other words, why do we add parts two
[07:13] In other words, why do we add parts two and three to the P value?
[07:16] and three to the P value? We add part two, the probability of
[07:19] We add part two, the probability of something else that is equally rare,
[07:21] something else that is equally rare, because although getting two heads might
[07:24] because although getting two heads might seem special,
[07:25] seem special, it doesn't seem as special when we know
[07:27] it doesn't seem as special when we know that other things are just as rare.
[07:31] that other things are just as rare. For example, imagine giving a loved one
[07:34] For example, imagine giving a loved one a flower and saying, "This is the rarest
[07:37] a flower and saying, "This is the rarest flower of this species. None are equally
[07:40] flower of this species. None are equally as rare."
[07:42] as rare." Chances are, your loved one would think
[07:45] Chances are, your loved one would think that the flower was super special.
[07:48] that the flower was super special. You might even get a kiss on the cheek.
[07:51] You might even get a kiss on the cheek. Now imagine saying to your loved one,
[07:53] Now imagine saying to your loved one, "This flower is equally as rare as all
[07:56] "This flower is equally as rare as all of these other flowers."
[07:59] of these other flowers." In this case, your loved one might not
[08:01] In this case, your loved one might not think the flower is very special. Wah,
[08:04] think the flower is very special. Wah, wah.
[08:05] wah. Note, even though these flowers are
[08:08] Note, even though these flowers are different colors, just knowing that they
[08:10] different colors, just knowing that they were equally rare would be a bummer.
[08:13] were equally rare would be a bummer. Because a lot of equally rare things
[08:16] Because a lot of equally rare things would make something less special, we
[08:18] would make something less special, we add part two to the P value.
[08:22] add part two to the P value. And we add rarer things to the P value
[08:24] And we add rarer things to the P value for a similar reason.
[08:27] for a similar reason. Going back to our flower example,
[08:29] Going back to our flower example, imagine telling your loved one, "This is
[08:32] imagine telling your loved one, "This is the rarest flower of this species. None
[08:35] the rarest flower of this species. None are rarer."
[08:37] are rarer." Again, there's a good chance your loved
[08:40] Again, there's a good chance your loved one would think that the flower was
[08:41] one would think that the flower was super special.
[08:43] super special. Now imagine saying, "There are a lot of
[08:46] Now imagine saying, "There are a lot of flowers that are rarer than this one."
[08:49] flowers that are rarer than this one." In this case, your loved one might not
[08:51] In this case, your loved one might not think the flower is very special.
[08:54] think the flower is very special. Wah, wah.
[08:56] Wah, wah. And like before, even though these
[08:58] And like before, even though these flowers are all different colors, just
[09:01] flowers are all different colors, just knowing they are rarer would be a
[09:02] knowing they are rarer would be a bummer.
[09:04] bummer. Thus, because rarer things make
[09:07] Thus, because rarer things make something less special, we add part
[09:09] something less special, we add part three to the P value.
[09:12] three to the P value. Okay, now that we know that getting two
[09:15] Okay, now that we know that getting two heads in a row is not very special or
[09:17] heads in a row is not very special or statistically significant,
[09:20] statistically significant, what about getting four heads and one
[09:22] what about getting four heads and one tails?
[09:24] tails? Would that suggest that our coin is
[09:26] Would that suggest that our coin is special?
[09:28] special? In other words, we can calculate a P
[09:30] In other words, we can calculate a P value to test this hypothesis.
[09:34] value to test this hypothesis. Even though I got four heads and one
[09:36] Even though I got four heads and one tails, my coin is no different from a
[09:39] tails, my coin is no different from a normal coin.
[09:41] normal coin. Again, although we want to know if the
[09:43] Again, although we want to know if the coin is special, the null hypothesis
[09:46] coin is special, the null hypothesis focuses on a normal coin.
[09:49] focuses on a normal coin. But if we get a small P value and reject
[09:52] But if we get a small P value and reject the null hypothesis, we will know that
[09:54] the null hypothesis, we will know that our coin is special.
[09:57] our coin is special. So, let's calculate the P value for
[09:59] So, let's calculate the P value for getting four heads and one tails.
[10:03] getting four heads and one tails. First, we know that it is possible to
[10:05] First, we know that it is possible to flip a coin five times and get heads
[10:08] flip a coin five times and get heads each time.
[10:10] each time. So, let's keep track of that with five
[10:12] So, let's keep track of that with five blue H's.
[10:14] blue H's. We can also flip a coin five times and
[10:17] We can also flip a coin five times and get four heads and one tails.
[10:20] get four heads and one tails. Note, there are five different ways to
[10:22] Note, there are five different ways to get four heads and one tails, but we
[10:25] get four heads and one tails, but we treat them all the same because the
[10:27] treat them all the same because the order of heads and tails doesn't matter.
[10:30] order of heads and tails doesn't matter. Likewise, there are 10 ways that we can
[10:33] Likewise, there are 10 ways that we can flip a coin and get three heads and two
[10:35] flip a coin and get three heads and two tails.
[10:37] tails. And 10 ways to get two heads and three
[10:40] And 10 ways to get two heads and three tails.
[10:42] tails. And five ways to get one heads and four
[10:44] And five ways to get one heads and four tails.
[10:46] tails. And lastly, one way to flip a coin five
[10:50] And lastly, one way to flip a coin five times and get five tails.
[10:53] times and get five tails. All in all, when we flip a coin five
[10:56] All in all, when we flip a coin five times, there are 32 possible outcomes.
[11:00] times, there are 32 possible outcomes. The P value for getting four heads and
[11:02] The P value for getting four heads and one tails is
[11:05] one tails is the probability we randomly get four
[11:07] the probability we randomly get four heads and one tails.
[11:10] heads and one tails. This is 5 / 32 since five of the 32
[11:14] This is 5 / 32 since five of the 32 outcomes had four heads and one tails.
[11:18] outcomes had four heads and one tails. Plus, the probability we randomly get
[11:21] Plus, the probability we randomly get something else that is equally rare.
[11:24] something else that is equally rare. This is 5 / 32 since five of the 32
[11:28] This is 5 / 32 since five of the 32 outcomes had one head and four tails.
[11:32] outcomes had one head and four tails. Plus, the probability we randomly get
[11:35] Plus, the probability we randomly get something rarer or more extreme.
[11:39] something rarer or more extreme. This is 2 / 32. Because both five heads
[11:43] This is 2 / 32. Because both five heads and five tails only occurred once each,
[11:46] and five tails only occurred once each, they are rarer than four heads and one
[11:49] they are rarer than four heads and one tails.
[11:50] tails. Thus, the P value for getting four heads
[11:53] Thus, the P value for getting four heads and one tails is 0.375.
[11:58] Again, we typically only reject the null
[12:01] Again, we typically only reject the null hypothesis if the P value is less than
[12:04] hypothesis if the P value is less than 0.05.
[12:06] 0.05. So, in this case, we will fail to reject
[12:10] So, in this case, we will fail to reject the null hypothesis.
[12:13] the null hypothesis. In other words, the data, getting four
[12:15] In other words, the data, getting four heads and one tails, did not convince us
[12:18] heads and one tails, did not convince us that our coin was special.
[12:22] that our coin was special. With coin tosses, it's pretty easy to
[12:24] With coin tosses, it's pretty easy to calculate probabilities and P values
[12:27] calculate probabilities and P values because it's pretty easy to list all of
[12:29] because it's pretty easy to list all of the possible outcomes.
[12:32] the possible outcomes. But, what if we wanted to calculate
[12:33] But, what if we wanted to calculate probabilities and P values for how tall
[12:36] probabilities and P values for how tall or short people are?
[12:39] or short people are? In theory, we could try to list every
[12:42] In theory, we could try to list every single possible value for height.
[12:45] single possible value for height. However, in practice, when we calculate
[12:48] However, in practice, when we calculate probabilities and P values for something
[12:50] probabilities and P values for something continuous like height, we usually use
[12:53] continuous like height, we usually use something called a statistical
[12:55] something called a statistical distribution.
[12:57] distribution. Here we have a distribution of height
[12:59] Here we have a distribution of height measurements from Brazilian women
[13:01] measurements from Brazilian women between 15 and 49 years old taken in
[13:05] between 15 and 49 years old taken in 1996.
[13:08] 1996. The red area under the curve indicates
[13:10] The red area under the curve indicates the probability that a person's height
[13:13] the probability that a person's height will be within a range of possible
[13:15] will be within a range of possible values.
[13:17] values. For example, 95% of the area under the
[13:20] For example, 95% of the area under the curve is between 142 and 169.
[13:25] curve is between 142 and 169. And that means that 95% of the Brazilian
[13:28] And that means that 95% of the Brazilian women were between 142
[13:31] women were between 142 and 169 cm tall.
[13:34] and 169 cm tall. In other words, there is a 95%
[13:37] In other words, there is a 95% probability that each time we measure a
[13:39] probability that each time we measure a Brazilian woman, their height will be
[13:42] Brazilian woman, their height will be between 142
[13:44] between 142 and 169 cm.
[13:48] and 169 cm. 2.5% of the total area under the curve
[13:51] 2.5% of the total area under the curve is greater than 169.
[13:54] is greater than 169. And that means there is a 2.5%
[13:57] And that means there is a 2.5% probability that each time we measure a
[13:59] probability that each time we measure a Brazilian woman, their height will be
[14:01] Brazilian woman, their height will be greater than 169 cm.
[14:05] greater than 169 cm. Likewise, 2.5% of the total area under
[14:09] Likewise, 2.5% of the total area under the curve is less than 142.
[14:13] the curve is less than 142. Thus, there's a 2.5% probability that
[14:16] Thus, there's a 2.5% probability that each time we measure a Brazilian woman,
[14:19] each time we measure a Brazilian woman, their height will be less than 142 cm.
[14:24] their height will be less than 142 cm. To calculate P values with a
[14:26] To calculate P values with a distribution, you add up the percentages
[14:28] distribution, you add up the percentages of area under the curve.
[14:31] of area under the curve. For example, imagine we measured someone
[14:34] For example, imagine we measured someone who is 142 cm tall.
[14:38] who is 142 cm tall. If we measured someone who is 142 cm
[14:41] If we measured someone who is 142 cm tall, we might wonder if it came from
[14:44] tall, we might wonder if it came from this distribution of heights, which has
[14:46] this distribution of heights, which has an average value of 155.7.
[14:50] Or if it came from another distribution
[14:53] Or if it came from another distribution of heights. For example, this green
[14:56] of heights. For example, this green distribution has an average value of
[14:57] distribution has an average value of 142.
[15:00] 142. So, the question is, is this
[15:02] So, the question is, is this measurement, 142 cm, so far away from
[15:06] measurement, 142 cm, so far away from the mean of the blue distribution that
[15:09] the mean of the blue distribution that we can reject the idea that it came from
[15:11] we can reject the idea that it came from it?
[15:13] it? If so, then that would suggest that
[15:15] If so, then that would suggest that another distribution, like this green
[15:17] another distribution, like this green one, might do a better job explaining
[15:20] one, might do a better job explaining the data.
[15:22] the data. The P value for the hypothesis, this
[15:24] The P value for the hypothesis, this measurement comes from the blue
[15:26] measurement comes from the blue distribution,
[15:28] distribution, starts with the 2.5% of the area for
[15:31] starts with the 2.5% of the area for people less than or equal to 142 cm.
[15:35] people less than or equal to 142 cm. Note, when we are working with a
[15:37] Note, when we are working with a distribution, we are interested in
[15:40] distribution, we are interested in adding more extreme values to the P
[15:42] adding more extreme values to the P value, rather than rarer values.
[15:45] value, rather than rarer values. In this case, all heights further than
[15:48] In this case, all heights further than 142 cm from the mean are considered more
[15:52] 142 cm from the mean are considered more extreme than what we observed.
[15:56] extreme than what we observed. We also add the 2.5% of the area for
[15:59] We also add the 2.5% of the area for people 169 cm or taller.
[16:03] people 169 cm or taller. Note, just like on the other side of the
[16:06] Note, just like on the other side of the distribution, these values are
[16:08] distribution, these values are considered equal to or more extreme
[16:10] considered equal to or more extreme because they are as far from the mean or
[16:13] because they are as far from the mean or further.
[16:15] further. Now, we just do the math
[16:17] Now, we just do the math and get 0.05.
[16:21] So, the P value for the hypothesis, someone 142 cm tall could come from the
[16:27] someone 142 cm tall could come from the blue distribution, is 0.05.
[16:31] blue distribution, is 0.05. And since the cutoff for significance is
[16:34] And since the cutoff for significance is usually 0.05,
[16:36] usually 0.05, we would say,
[16:38] we would say, "Hmm,
[16:40] "Hmm, maybe it could come from this
[16:41] maybe it could come from this distribution, maybe not. It's hard to
[16:44] distribution, maybe not. It's hard to tell since the P value is right on the
[16:46] tell since the P value is right on the borderline."
[16:48] borderline." So, maybe they come from this
[16:50] So, maybe they come from this distribution
[16:51] distribution or maybe they come from this
[16:53] or maybe they come from this distribution. The data are inconclusive.
[16:56] distribution. The data are inconclusive. Wah, wah.
[16:59] Wah, wah. Note, if we had measured someone who was
[17:01] Note, if we had measured someone who was 141 cm tall, so just a little bit
[17:05] 141 cm tall, so just a little bit shorter than 142 cm,
[17:08] shorter than 142 cm, then the P value would be 0.016
[17:12] plus 0.016,
[17:16] which equals 0.03.
[17:19] which equals 0.03. And since 0.03
[17:21] And since 0.03 is less than 0.05,
[17:24] is less than 0.05, the standard threshold, we can reject
[17:26] the standard threshold, we can reject the hypothesis that given the blue
[17:29] the hypothesis that given the blue distribution, it is normal to measure
[17:31] distribution, it is normal to measure someone 141 cm tall.
[17:35] someone 141 cm tall. Thus, we will conclude that it's pretty
[17:38] Thus, we will conclude that it's pretty special to measure someone that short.
[17:41] special to measure someone that short. And that suggests that a different
[17:43] And that suggests that a different distribution of heights makes more
[17:45] distribution of heights makes more sense.
[17:47] sense. Now, what if we measured someone who is
[17:50] Now, what if we measured someone who is between 155.4
[17:53] between 155.4 and 156 cm tall?
[17:57] and 156 cm tall? Note, the peak of the curve is right at
[17:59] Note, the peak of the curve is right at the average height, so we are asking
[18:02] the average height, so we are asking is a measurement between 155.4
[18:06] is a measurement between 155.4 and 156
[18:08] and 156 so far away from the mean of the blue
[18:10] so far away from the mean of the blue distribution that we can reject the idea
[18:12] distribution that we can reject the idea that it came from it?
[18:15] that it came from it? If the P value is small, then that
[18:17] If the P value is small, then that suggests that some other distribution
[18:19] suggests that some other distribution would do a better job explaining the
[18:21] would do a better job explaining the data.
[18:23] data. Note, the probability of someone being
[18:26] Note, the probability of someone being between 155.4
[18:28] between 155.4 and 156 cm is only 0.04.
[18:33] and 156 cm is only 0.04. The red area is pretty small, barely a
[18:36] The red area is pretty small, barely a line.
[18:38] line. So, 0.04
[18:40] So, 0.04 is the first part of calculating the P
[18:43] is the first part of calculating the P value since given this distribution of
[18:46] value since given this distribution of heights, that is the probability that we
[18:48] heights, that is the probability that we would randomly measure someone in this
[18:50] would randomly measure someone in this range of values.
[18:53] range of values. Now, we need to figure out the more
[18:55] Now, we need to figure out the more extreme parts.
[18:57] extreme parts. On the left side, all of the heights
[18:59] On the left side, all of the heights less than 155.4
[19:02] less than 155.4 are further from the mean.
[19:04] are further from the mean. Thus, they are more extreme.
[19:08] Thus, they are more extreme. And because 48% of the area under the
[19:11] And because 48% of the area under the curve is for heights less than 155.4,
[19:15] curve is for heights less than 155.4, we add 0.48
[19:17] we add 0.48 to the P value.
[19:19] to the P value. On the right side, all of the heights
[19:22] On the right side, all of the heights greater than 156 are further from the
[19:24] greater than 156 are further from the mean. Thus, they are all more extreme.
[19:30] mean. Thus, they are all more extreme. And because 48% of the area under the
[19:32] And because 48% of the area under the curve is for heights greater than 156,
[19:36] curve is for heights greater than 156, we add 0.48
[19:38] we add 0.48 to the P value.
[19:40] to the P value. Ultimately, we end up adding all of the
[19:43] Ultimately, we end up adding all of the area under the curve, so the P value
[19:46] area under the curve, so the P value equals 1.
[19:48] equals 1. So, this means that given this
[19:51] So, this means that given this distribution of heights, we would not
[19:53] distribution of heights, we would not find it unusual to measure someone whose
[19:55] find it unusual to measure someone whose height was close to the average, even
[19:58] height was close to the average, even though the probability is small.
[20:01] though the probability is small. In other words, the data does not
[20:03] In other words, the data does not suggest that another distribution would
[20:06] suggest that another distribution would do a better job explaining the data.
[20:09] do a better job explaining the data. Bam.
[20:12] Bam. So far, we've only talked about
[20:14] So far, we've only talked about two-sided P values.
[20:16] two-sided P values. Now, I'll give you an example of a
[20:18] Now, I'll give you an example of a one-sided P value and tell you why it
[20:21] one-sided P value and tell you why it has the potential to be dangerous.
[20:24] has the potential to be dangerous. Imagine we measured how long it took a
[20:26] Imagine we measured how long it took a bunch of people to recover from an
[20:28] bunch of people to recover from an illness.
[20:29] illness. Now, imagine we created a new drug,
[20:32] Now, imagine we created a new drug, super drug, and wanted to see if it
[20:34] super drug, and wanted to see if it helped people recover in fewer days.
[20:38] helped people recover in fewer days. If we gave super drug to a bunch of
[20:40] If we gave super drug to a bunch of people and the average recovery was 4.5
[20:43] people and the average recovery was 4.5 days,
[20:45] days, then a two-sided P value, like the ones
[20:47] then a two-sided P value, like the ones we've been computing all along, would be
[20:51] we've been computing all along, would be the sum of this area under the curve,
[20:53] the sum of this area under the curve, 0.016,
[20:56] 0.016, plus this area under the curve, 0.016.
[21:01] plus this area under the curve, 0.016. And the total is 0.03.
[21:05] And the total is 0.03. And since 0.03 is less than 0.05,
[21:10] And since 0.03 is less than 0.05, the two-sided p-value tells us that,
[21:12] the two-sided p-value tells us that, given this distribution of recovery
[21:14] given this distribution of recovery times, super drug did something unusual.
[21:19] times, super drug did something unusual. And that suggests that some other
[21:21] And that suggests that some other distribution does a better job
[21:22] distribution does a better job explaining the data.
[21:25] explaining the data. For a one-sided p-value, the first thing
[21:28] For a one-sided p-value, the first thing we do is decide which direction we want
[21:30] we do is decide which direction we want to see change in.
[21:32] to see change in. In this case, we'd like super drug to
[21:35] In this case, we'd like super drug to shorten the time it takes to recover
[21:37] shorten the time it takes to recover from the illness.
[21:39] from the illness. So, that means we want to see if
[21:41] So, that means we want to see if recovery times are shorter.
[21:44] recovery times are shorter. Because we want to see change in this
[21:45] Because we want to see change in this direction, the only more extreme values
[21:49] direction, the only more extreme values are less than 4.5 days.
[21:52] are less than 4.5 days. All of the values greater than 4.5 days
[21:55] All of the values greater than 4.5 days are considered less extreme.
[21:58] are considered less extreme. So, when we calculate a one-sided
[22:01] So, when we calculate a one-sided p-value, we only use the area that is in
[22:04] p-value, we only use the area that is in the direction we want to see change,
[22:06] the direction we want to see change, 0.016.
[22:10] Again, since 0.016
[22:13] Again, since 0.016 is less than 0.05,
[22:16] is less than 0.05, the one-sided p-value would tell us
[22:18] the one-sided p-value would tell us that, given this distribution, super
[22:21] that, given this distribution, super drug did something unusual.
[22:24] drug did something unusual. And that some other distribution makes
[22:26] And that some other distribution makes more sense.
[22:29] more sense. Now, imagine that super drug wasn't so
[22:31] Now, imagine that super drug wasn't so super, and on average, it took 15.5 days
[22:36] super, and on average, it took 15.5 days to recover.
[22:39] to recover. Just like before, the two-sided p-value
[22:41] Just like before, the two-sided p-value would be
[22:43] would be the sum of this area under the curve,
[22:45] the sum of this area under the curve, 0.016,
[22:48] 0.016, plus this area under the curve, 0.016.
[22:53] plus this area under the curve, 0.016. And the total is 0.03.
[22:57] And the total is 0.03. In other words, regardless of whether
[22:59] In other words, regardless of whether super drug is super and makes things
[23:01] super drug is super and makes things better, or if it is not so super and
[23:04] better, or if it is not so super and makes things worse, a two-sided p-value
[23:07] makes things worse, a two-sided p-value will detect something unusual happened.
[23:11] will detect something unusual happened. For a one-sided p-value, the first thing
[23:13] For a one-sided p-value, the first thing we do is decide which direction we want
[23:16] we do is decide which direction we want to see change in.
[23:18] to see change in. And just like before, that means we want
[23:21] And just like before, that means we want to see if recovery times are shorter.
[23:24] to see if recovery times are shorter. So the one-sided p-value is this huge
[23:27] So the one-sided p-value is this huge area, 0.98,
[23:30] area, 0.98, because it is more extreme in the
[23:32] because it is more extreme in the direction we want to see change.
[23:35] direction we want to see change. And since 0.98
[23:37] And since 0.98 is greater than 0.05,
[23:40] is greater than 0.05, the one-sided p-value would not detect
[23:42] the one-sided p-value would not detect that super drug was doing anything
[23:45] that super drug was doing anything unusual.
[23:47] unusual. In other words, the one-sided p-value is
[23:50] In other words, the one-sided p-value is only looking to see if a distribution to
[23:52] only looking to see if a distribution to the left of the original mean makes more
[23:54] the left of the original mean makes more sense.
[23:56] sense. And since the observation is on the
[23:58] And since the observation is on the right side of the mean, we fail to
[24:00] right side of the mean, we fail to reject the hypothesis that the original
[24:02] reject the hypothesis that the original distribution makes sense.
[24:05] distribution makes sense. And since failing to detect that super
[24:08] And since failing to detect that super drug is making things worse would be
[24:10] drug is making things worse would be bad, one-sided p-values are tricky and
[24:13] bad, one-sided p-values are tricky and should be avoided or only used by
[24:15] should be avoided or only used by experts who really know what they're
[24:17] experts who really know what they're doing.
[24:19] doing. Bam!
[24:20] Bam! In summary, a p-value is composed of
[24:23] In summary, a p-value is composed of three parts.
[24:25] three parts. The first part is the probability random
[24:27] The first part is the probability random chance would result in the observation.
[24:31] chance would result in the observation. The second part is the probability of
[24:33] The second part is the probability of observing something else that is equally
[24:35] observing something else that is equally rare.
[24:37] rare. And the third part is the probability of
[24:40] And the third part is the probability of observing something rarer or more
[24:42] observing something rarer or more extreme.
[24:44] extreme. Bam!
[24:47] Bam! Hooray! We've made it to the end of
[24:49] Hooray! We've made it to the end of another exciting StatQuest. If you like
[24:52] another exciting StatQuest. If you like this StatQuest and want to see more,
[24:54] this StatQuest and want to see more, please subscribe.
[24:56] please subscribe. And if you want to support StatQuest,
[24:58] And if you want to support StatQuest, consider contributing to my Patreon
[25:00] consider contributing to my Patreon campaign, becoming a channel member,
[25:03] campaign, becoming a channel member, buying one or two of my original songs
[25:05] buying one or two of my original songs or a t-shirt or a hoodie, or just
[25:07] or a t-shirt or a hoodie, or just donate. The links are in the description
[25:10] donate. The links are in the description below.
[25:11] below. All right. Until next time, quest on.
