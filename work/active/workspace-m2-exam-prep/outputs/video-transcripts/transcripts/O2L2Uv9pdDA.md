---
video_id: O2L2Uv9pdDA
url: https://www.youtube.com/watch?v=O2L2Uv9pdDA
title: Naive Bayes, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 15:12
language: en
unit: L04
status: OK
---

[00:00] I'm at home during lockdown, working on
[00:04] I'm at home during lockdown, working on my StatQuest, yeah.
[00:06] my StatQuest, yeah. I'm at home during lockdown, working on
[00:09] I'm at home during lockdown, working on my StatQuest, yeah. StatQuest.
[00:14] my StatQuest, yeah. StatQuest. Hello, I'm Josh Starmer, and welcome to
[00:17] Hello, I'm Josh Starmer, and welcome to StatQuest. Today, we're going to talk
[00:19] StatQuest. Today, we're going to talk about naive Bayes, and it's going to be
[00:22] about naive Bayes, and it's going to be clearly explained.
[00:24] clearly explained. This StatQuest is sponsored by Jad Bio,
[00:28] This StatQuest is sponsored by Jad Bio, just add data, and their automatic
[00:30] just add data, and their automatic machine learning algorithms will do the
[00:32] machine learning algorithms will do the rest of the work for you.
[00:34] rest of the work for you. For more details, follow the link in the
[00:37] For more details, follow the link in the pinned comment below.
[00:39] pinned comment below. Note, when most people want to learn
[00:42] Note, when most people want to learn about naive Bayes, they want to learn
[00:44] about naive Bayes, they want to learn about the multinomial naive Bayes
[00:46] about the multinomial naive Bayes classifier, and that's what we talk
[00:49] classifier, and that's what we talk about in this video.
[00:50] about in this video. However, just know that there is another
[00:53] However, just know that there is another commonly used version of naive Bayes
[00:56] commonly used version of naive Bayes called Gaussian naive Bayes
[00:57] called Gaussian naive Bayes classification, and I cover that in a
[01:00] classification, and I cover that in a follow-up StatQuest.
[01:02] follow-up StatQuest. So, check that one out when you're done
[01:04] So, check that one out when you're done with this quest.
[01:06] with this quest. Bam.
[01:08] Bam. Now, imagine we receive normal messages
[01:11] Now, imagine we receive normal messages from friends and family,
[01:13] from friends and family, and we also receive spam, unwanted
[01:16] and we also receive spam, unwanted messages that are usually scams or
[01:18] messages that are usually scams or unsolicited advertisements,
[01:21] unsolicited advertisements, and we wanted to filter out the spam
[01:23] and we wanted to filter out the spam messages.
[01:25] messages. So, the first thing we do is make a
[01:28] So, the first thing we do is make a histogram of all the words that occur in
[01:30] histogram of all the words that occur in the normal messages from friends and
[01:32] the normal messages from friends and family.
[01:34] family. We can use the histogram to calculate
[01:36] We can use the histogram to calculate the probabilities of seeing each word
[01:39] the probabilities of seeing each word given that it was in a normal message.
[01:42] given that it was in a normal message. For example, the probability we see the
[01:45] For example, the probability we see the word deer
[01:47] word deer given that we saw it in a normal message
[01:50] given that we saw it in a normal message is eight, the total number of times deer
[01:53] is eight, the total number of times deer occurred in normal messages,
[01:56] occurred in normal messages, divided by 17, the total number of words
[01:59] divided by 17, the total number of words in all of the normal messages.
[02:03] in all of the normal messages. And that gives us 0.47.
[02:07] And that gives us 0.47. So, let's put that over the word dear,
[02:09] So, let's put that over the word dear, so we don't forget it.
[02:11] so we don't forget it. Likewise, the probability that we see
[02:14] Likewise, the probability that we see the word friend
[02:16] the word friend given that we saw it in a normal message
[02:20] given that we saw it in a normal message is five, the total number of times
[02:22] is five, the total number of times friend occurred in normal messages
[02:25] friend occurred in normal messages divided by 17, the total number of words
[02:29] divided by 17, the total number of words in all of the normal messages.
[02:32] in all of the normal messages. And that gives us 0.29.
[02:35] And that gives us 0.29. So, let's put that over the word friend,
[02:38] So, let's put that over the word friend, so we don't forget it.
[02:40] so we don't forget it. Likewise, the probability that we see
[02:42] Likewise, the probability that we see the word launch given that it is in a
[02:44] the word launch given that it is in a normal message is 0.18.
[02:48] normal message is 0.18. And the probability that we see the word
[02:50] And the probability that we see the word money given that it is in a normal
[02:53] money given that it is in a normal message is 0.06.
[02:57] message is 0.06. Now, we make a histogram of all the
[02:59] Now, we make a histogram of all the words that occur in the spam
[03:02] words that occur in the spam and calculate the probability of seeing
[03:04] and calculate the probability of seeing the word dear
[03:06] the word dear given that we saw it in the spam.
[03:10] given that we saw it in the spam. And that is two, the number of times we
[03:12] And that is two, the number of times we saw dear in the spam
[03:15] saw dear in the spam divided by seven, the total number of
[03:17] divided by seven, the total number of words in the spam.
[03:20] words in the spam. And that gives us 0.29.
[03:24] Likewise, we calculate the probability of seeing the remaining words given that
[03:28] of seeing the remaining words given that they were in the spam.
[03:31] they were in the spam. Bam!
[03:34] Now, because these histograms are taking
[03:37] Now, because these histograms are taking up a lot of space, let's get rid of
[03:39] up a lot of space, let's get rid of them, but keep the probabilities.
[03:42] them, but keep the probabilities. Oh, no! It's the dreaded terminology
[03:45] Oh, no! It's the dreaded terminology alert.
[03:47] alert. Because we have calculated the
[03:48] Because we have calculated the probabilities of discrete individual
[03:51] probabilities of discrete individual words and not the probability of
[03:53] words and not the probability of something continuous like weight or
[03:55] something continuous like weight or height. These probabilities are also
[03:58] height. These probabilities are also called likelihoods.
[04:01] called likelihoods. I mention this because some tutorials
[04:04] I mention this because some tutorials say these are probabilities, and others
[04:06] say these are probabilities, and others say they are likelihoods.
[04:09] say they are likelihoods. In this case, the terms are
[04:10] In this case, the terms are interchangeable, so don't sweat it.
[04:14] interchangeable, so don't sweat it. We'll talk more about probabilities
[04:16] We'll talk more about probabilities versus likelihoods when we talk about
[04:18] versus likelihoods when we talk about Gaussian naive Bayes in the follow-up
[04:21] Gaussian naive Bayes in the follow-up quest.
[04:22] quest. Now, imagine we got a new message that
[04:25] Now, imagine we got a new message that said,
[04:26] said, "Dear friend."
[04:29] "Dear friend." And we want to decide if it is a normal
[04:31] And we want to decide if it is a normal message or spam.
[04:34] message or spam. We start with an initial guess about the
[04:36] We start with an initial guess about the probability that any message, regardless
[04:39] probability that any message, regardless of what it says, is a normal message.
[04:43] of what it says, is a normal message. This guess can be any probability that
[04:45] This guess can be any probability that we want, but a common guess is estimated
[04:48] we want, but a common guess is estimated from the training data.
[04:50] from the training data. For example, since eight of the 12
[04:53] For example, since eight of the 12 messages are normal messages, our
[04:55] messages are normal messages, our initial guess will be 0.67.
[04:59] initial guess will be 0.67. So, let's put that under the normal
[05:01] So, let's put that under the normal messages so we don't forget it.
[05:04] messages so we don't forget it. Oh, no! It's another dreaded terminology
[05:07] Oh, no! It's another dreaded terminology alert.
[05:08] alert. The initial guess that we observe a
[05:10] The initial guess that we observe a normal message is called a prior
[05:12] normal message is called a prior probability.
[05:15] probability. Now, we multiply the initial guess by
[05:17] Now, we multiply the initial guess by the probability that the word "dear"
[05:19] the probability that the word "dear" occurs in a normal message,
[05:22] occurs in a normal message, and the probability that the word
[05:24] and the probability that the word "friend" occurs in a normal message.
[05:28] "friend" occurs in a normal message. Now, we just plug in the values that we
[05:30] Now, we just plug in the values that we worked out earlier and do the math.
[05:33] worked out earlier and do the math. Beep boop beep boop beep.
[05:35] Beep boop beep boop beep. And we get 0.09.
[05:39] We can think of 0.09
[05:42] We can think of 0.09 as the score that "dear friend" gets if
[05:44] as the score that "dear friend" gets if it is a normal message.
[05:47] it is a normal message. However, technically, it is proportional
[05:50] However, technically, it is proportional to the probability that the message is
[05:52] to the probability that the message is normal given that it says dear friend.
[05:56] normal given that it says dear friend. So, let's put that on top of the normal
[05:58] So, let's put that on top of the normal messages so we don't forget.
[06:01] messages so we don't forget. Now, just like we did before, we start
[06:04] Now, just like we did before, we start with an initial guess about the
[06:06] with an initial guess about the probability that any message, regardless
[06:08] probability that any message, regardless of what it says, is spam.
[06:12] of what it says, is spam. And just like before, the guess can be
[06:14] And just like before, the guess can be any probability we want, but a common
[06:17] any probability we want, but a common guess is estimated from the training
[06:19] guess is estimated from the training data.
[06:21] data. And since four of the 12 messages are
[06:23] And since four of the 12 messages are spam, our initial guess will be 0.33.
[06:29] So, let's put that under the spam so we don't forget it.
[06:33] don't forget it. Now, we multiply that initial guess by
[06:36] Now, we multiply that initial guess by the probability that the word dear
[06:38] the probability that the word dear occurs in spam.
[06:40] occurs in spam. And the probability that the word friend
[06:43] And the probability that the word friend occurs in spam.
[06:46] occurs in spam. Now, we just plugged in the values that
[06:47] Now, we just plugged in the values that we worked out earlier and do the math.
[06:51] we worked out earlier and do the math. Beep, boop, beep, boop, beep.
[06:53] Beep, boop, beep, boop, beep. And we get 0.01.
[06:57] Like before, we can think of 0.01
[07:00] Like before, we can think of 0.01 as the score that dear friend gets if it
[07:03] as the score that dear friend gets if it is spam.
[07:05] is spam. However, technically, it is proportional
[07:09] However, technically, it is proportional to the probability that the message is
[07:11] to the probability that the message is spam given that it says dear friend.
[07:15] spam given that it says dear friend. And because the score we got for normal
[07:17] And because the score we got for normal message, 0.09,
[07:20] message, 0.09, is greater than the score we got for
[07:22] is greater than the score we got for spam, 0.01,
[07:25] spam, 0.01, we will decide that dear friend is a
[07:28] we will decide that dear friend is a normal message.
[07:30] normal message. Double bam!
[07:33] Double bam! Now, before we move on to a slightly
[07:36] Now, before we move on to a slightly more complex situation, let's review
[07:38] more complex situation, let's review what we've done so far.
[07:41] what we've done so far. We started with histograms of all the
[07:43] We started with histograms of all the words in the normal messages
[07:46] words in the normal messages and all of the words in the spam.
[07:49] and all of the words in the spam. Then we calculated the probabilities of
[07:51] Then we calculated the probabilities of seeing each word given that we saw the
[07:53] seeing each word given that we saw the word in either a normal message or spam.
[07:57] word in either a normal message or spam. Then we made an initial guess about the
[07:59] Then we made an initial guess about the probability of seeing a normal message.
[08:03] probability of seeing a normal message. This guess can be anything between zero
[08:06] This guess can be anything between zero and one, but we based ours on the
[08:08] and one, but we based ours on the classifications in the training data
[08:10] classifications in the training data set.
[08:12] set. Then we made the same sort of guess
[08:14] Then we made the same sort of guess about the probability of seeing spam.
[08:17] about the probability of seeing spam. Then we multiplied our initial guess
[08:19] Then we multiplied our initial guess that the message was normal
[08:22] that the message was normal by the probabilities of seeing the words
[08:24] by the probabilities of seeing the words dear and friend given that the message
[08:26] dear and friend given that the message was normal.
[08:28] was normal. Then we multiplied our initial guess
[08:30] Then we multiplied our initial guess that the message was spam
[08:33] that the message was spam by the probabilities of seeing the words
[08:35] by the probabilities of seeing the words dear and friend given that the message
[08:38] dear and friend given that the message was spam.
[08:40] was spam. Then we did the math and decided that
[08:42] Then we did the math and decided that dear friend was a normal message because
[08:44] dear friend was a normal message because 0.09
[08:46] 0.09 is greater than 0.01.
[08:50] Now that we understand the basics of how naive Bayes classification works,
[08:56] naive Bayes classification works, let's look at a slightly more
[08:57] let's look at a slightly more complicated example.
[09:00] complicated example. This time, let's try to classify this
[09:03] This time, let's try to classify this message: lunch money money money money.
[09:08] message: lunch money money money money. Note, this message contains the word
[09:10] Note, this message contains the word money four times.
[09:13] money four times. And since the probability of seeing the
[09:15] And since the probability of seeing the word money is much higher in spam than
[09:19] word money is much higher in spam than in normal messages,
[09:21] in normal messages, then it seems reasonable to predict that
[09:23] then it seems reasonable to predict that this message will end up being spam.
[09:27] this message will end up being spam. So, let's do the math.
[09:29] So, let's do the math. Calculating the score for a normal
[09:31] Calculating the score for a normal message works just like before.
[09:34] message works just like before. We start with the initial guess,
[09:37] We start with the initial guess, then we multiply it by the probability
[09:39] then we multiply it by the probability we see lunch given that it is in a
[09:41] we see lunch given that it is in a normal message.
[09:43] normal message. And the probability we see money four
[09:45] And the probability we see money four times given that it is in a normal
[09:48] times given that it is in a normal message.
[09:50] message. When we do the math, we get this tiny
[09:52] When we do the math, we get this tiny number.
[09:54] number. However, when we do the same calculation
[09:57] However, when we do the same calculation for spam,
[09:59] for spam, we get zero.
[10:02] we get zero. This is because the probability we see
[10:04] This is because the probability we see lunch in spam is zero since it was not
[10:07] lunch in spam is zero since it was not in the training data.
[10:10] in the training data. And when we plug in zero for the
[10:12] And when we plug in zero for the probability we see lunch given that it
[10:14] probability we see lunch given that it was in spam,
[10:16] was in spam, then it doesn't matter what value we
[10:18] then it doesn't matter what value we picked for the initial guess that the
[10:20] picked for the initial guess that the message was spam,
[10:22] message was spam, and it doesn't matter what the
[10:24] and it doesn't matter what the probability is that we see money given
[10:27] probability is that we see money given that the message was spam,
[10:30] that the message was spam, because anything times zero
[10:33] because anything times zero is zero.
[10:35] is zero. In other words, if a message contains
[10:38] In other words, if a message contains the word lunch, it will not be
[10:40] the word lunch, it will not be classified as spam.
[10:42] classified as spam. And that means we will always classify
[10:45] And that means we will always classify the messages with lunch in them as
[10:47] the messages with lunch in them as normal, no matter how many times we see
[10:49] normal, no matter how many times we see the word money.
[10:52] the word money. And that's a problem.
[10:55] And that's a problem. To work around this problem, people
[10:57] To work around this problem, people usually add one count represented by a
[11:00] usually add one count represented by a black box to each word in the
[11:02] black box to each word in the histograms.
[11:04] histograms. Note, the number of counts we add to
[11:07] Note, the number of counts we add to each word is typically referred to with
[11:09] each word is typically referred to with the Greek letter alpha.
[11:12] the Greek letter alpha. In this case, alpha equals one, but we
[11:15] In this case, alpha equals one, but we could have set it to anything.
[11:18] could have set it to anything. Anyway, now when we calculate the
[11:20] Anyway, now when we calculate the probabilities of observing each word, we
[11:23] probabilities of observing each word, we never get zero.
[11:26] never get zero. For example, the probability of seeing
[11:29] For example, the probability of seeing lunch given that it is in spam
[11:32] lunch given that it is in spam is 1 / 7 the total number of words in
[11:37] is 1 / 7 the total number of words in spam plus 4 the extra counts that we
[11:40] spam plus 4 the extra counts that we added.
[11:42] added. And that gives us 0.09.
[11:46] Note, adding counts to each word does
[11:49] Note, adding counts to each word does not change our initial guess that a
[11:51] not change our initial guess that a message is normal
[11:53] message is normal or the initial guess that the message is
[11:55] or the initial guess that the message is spam
[11:57] spam because adding a count to each word did
[11:59] because adding a count to each word did not change the number of messages in the
[12:02] not change the number of messages in the training data set that are normal
[12:04] training data set that are normal or the number of messages that are spam.
[12:08] or the number of messages that are spam. Now when we calculate the scores for
[12:11] Now when we calculate the scores for this message
[12:13] this message we still get a small number for the
[12:15] we still get a small number for the normal message
[12:17] normal message but now when we calculate the value for
[12:19] but now when we calculate the value for spam we get a value greater than zero.
[12:23] spam we get a value greater than zero. And since the value for spam is greater
[12:26] And since the value for spam is greater than the one for a normal message
[12:29] than the one for a normal message we classify the message as spam.
[12:32] we classify the message as spam. Spam.
[12:35] Now let's talk about why Naive Bayes is
[12:38] Now let's talk about why Naive Bayes is naive.
[12:40] naive. The thing that makes Naive Bayes so
[12:43] The thing that makes Naive Bayes so naive is that it treats all word orders
[12:46] naive is that it treats all word orders the same.
[12:48] the same. For example
[12:50] For example the normal message score for the phrase
[12:52] the normal message score for the phrase "dear friend"
[12:54] "dear friend" is the exact same for the score for
[12:57] is the exact same for the score for "friend dear".
[12:59] "friend dear". In other words, regardless of how the
[13:02] In other words, regardless of how the words are ordered we get 0.08.
[13:06] words are ordered we get 0.08. Treating all word orders equal is very
[13:09] Treating all word orders equal is very different from how you and I
[13:11] different from how you and I communicate.
[13:13] communicate. Every language has grammar rules and
[13:15] Every language has grammar rules and common phrases but Naive Bayes ignores
[13:18] common phrases but Naive Bayes ignores all of that stuff.
[13:21] all of that stuff. Instead Naive Bayes treats language like
[13:24] Instead Naive Bayes treats language like it is just a bag full of words and each
[13:26] it is just a bag full of words and each message is a random handful of them.
[13:30] message is a random handful of them. Naive Bayes ignores all the rules
[13:32] Naive Bayes ignores all the rules because keeping track of every single
[13:34] because keeping track of every single reasonable phrase in a language would be
[13:36] reasonable phrase in a language would be impossible.
[13:39] impossible. That said, even though Naive Bayes is
[13:41] That said, even though Naive Bayes is naive, it tends to perform surprisingly
[13:44] naive, it tends to perform surprisingly well when separating normal messages
[13:47] well when separating normal messages from spam.
[13:49] from spam. In machine learning lingo, we'd say that
[13:52] In machine learning lingo, we'd say that by ignoring relationships among words,
[13:55] by ignoring relationships among words, Naive Bayes has high bias.
[13:58] Naive Bayes has high bias. But, because it works well in practice,
[14:01] But, because it works well in practice, Naive Bayes has low variance.
[14:04] Naive Bayes has low variance. Shameless self-promotion.
[14:07] Shameless self-promotion. If you are not already familiar with the
[14:09] If you are not already familiar with the terms bias and variance, check out the
[14:12] terms bias and variance, check out the quest. The link is in the description
[14:14] quest. The link is in the description below.
[14:16] below. Triple spam.
[14:19] Triple spam. Oh, no! It's one last shameless
[14:22] Oh, no! It's one last shameless self-promotion.
[14:24] self-promotion. One awesome way to support StatQuest is
[14:26] One awesome way to support StatQuest is to purchase the Naive Bayes StatQuest
[14:29] to purchase the Naive Bayes StatQuest Study Guide. It has everything you need
[14:32] Study Guide. It has everything you need to study for an exam or job interview.
[14:35] to study for an exam or job interview. It's eight pages of total awesomeness.
[14:38] It's eight pages of total awesomeness. And while you're there, check out the
[14:40] And while you're there, check out the other StatQuest Study Guides. There's
[14:43] other StatQuest Study Guides. There's something for everyone.
[14:46] Hooray! We've made it to the end of another exciting StatQuest. If you like
[14:51] another exciting StatQuest. If you like this StatQuest and want to see more,
[14:53] this StatQuest and want to see more, please subscribe. And if you want to
[14:55] please subscribe. And if you want to support StatQuest, consider contributing
[14:57] support StatQuest, consider contributing to my Patreon campaign, becoming a
[14:59] to my Patreon campaign, becoming a channel member, buying one or two of my
[15:02] channel member, buying one or two of my original songs, or a t-shirt, or a
[15:04] original songs, or a t-shirt, or a hoodie, or just donate. The links are in
[15:06] hoodie, or just donate. The links are in the description below. All right. Until
[15:09] the description below. All right. Until next time, quest on.
