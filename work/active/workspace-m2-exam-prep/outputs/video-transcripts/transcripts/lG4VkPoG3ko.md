---
video_id: lG4VkPoG3ko
url: https://www.youtube.com/watch?v=lG4VkPoG3ko
title: The medical test paradox, and redesigning Bayes' rule
channel: 3Blue1Brown
duration: 21:13
language: en
unit: L01
status: OK
---

[00:00] Some of you may have heard this paradoxical fact about medical tests.
[00:03] It's very commonly used to introduce the topic of Bayes' rule in probability.
[00:07] The paradox is that you could take a test which is highly accurate,
[00:11] in the sense that it gives correct results to a large majority of the people taking it.
[00:16] And yet, under the right circumstances, when assessing the
[00:19] probability that your particular test result is correct,
[00:22] you can still land on a very low number, arbitrarily low, in fact.
[00:26] In short, an accurate test is not necessarily a very predictive test.
[00:33] Now when people think about math and formulas,
[00:35] they don't often think of it as a design process.
[00:38] I mean, maybe in the case of notation it's easy to see that different choices
[00:42] are possible, but when it comes to the structure of the formulas themselves
[00:45] and how we use them, that's something that people typically view as fixed.
[00:50] In this video, you and I will dig into this paradox,
[00:53] but instead of using it to talk about the usual version of Bayes' rule,
[00:57] I'd like to motivate an alternate version, an alternate design choice.
[01:01] Now, what's up on the screen now is a little bit abstract,
[01:04] which makes it difficult to justify that there really is a substantive difference here,
[01:08] especially when I haven't explained either one yet.
[01:11] To see what I'm talking about though, we should really start by spending some
[01:14] time a little more concretely, and just laying out what exactly this paradox is.
[01:24] Picture a thousand women and suppose that 1% of them have breast cancer.
[01:28] And let's say they all undergo a certain breast cancer screening,
[01:31] and that 9 of those with cancer correctly get positive results,
[01:35] and there's one false negative.
[01:37] And then suppose that among the remainder without cancer,
[01:41] 89 get false positives, and 901 correctly get negative results.
[01:45] So if all you know about a woman is that she does the screening and she gets a positive
[01:50] result, you don't have information about symptoms or anything like that,
[01:53] you know that she's either one of these 9 true positives or one of these 89 false
[01:57] positives.
[01:59] So the probability that she's in the cancer group given the test
[02:03] result is 9 divided by 9 plus 89, which is approximately 1 in 11.
[02:09] In medical parlance, you would call this the positive predictive value of the test,
[02:13] or PPV, the number of true positives divided by the total number of positive test results.
[02:18] You can see where the name comes from.
[02:20] To what extent does a positive test result actually predict that you have the disease?
[02:26] Now, hopefully, as I've presented it this way where we're thinking
[02:30] concretely about a sample population, all of this makes perfect sense.
[02:33] But where it comes across as counterintuitive is if you just look
[02:37] at the accuracy of the test, present it to people as a statistic,
[02:40] and then ask them to make judgments about their test result.
[02:44] Test accuracy is not actually one number, but two.
[02:46] First, you ask how often is the test correct on those with the disease.
[02:51] This is known as the test sensitivity, as in how
[02:54] sensitive is it to detecting the presence of the disease.
[02:58] In our example, test sensitivity is 9 in 10, or 90%.
[03:02] And another way to say the same fact would be to say the false negative rate is 10%.
[03:06] And then a separate, not necessarily related number is how often it's correct for those
[03:11] without the disease, which is known as the test specificity,
[03:15] as in are positive results caused specifically by the disease,
[03:18] or are there confounding triggers giving false positives.
[03:23] In our example, the specificity is about 91%.
[03:26] Or another way to say the same fact would be to say the false positive rate is 9%.
[03:31] So the paradox here is that in one sense, the test is over 90% accurate.
[03:37] It gives correct results to over 90% of the patients who take it.
[03:40] And yet, if you learn that someone gets a positive result without any added information,
[03:45] there's actually only a 1 in 11 chance that that particular result is accurate.
[03:50] This is a bit of a problem, because of all of the places for math to be counterintuitive,
[03:54] medical tests are one area where it matters a lot.
[03:57] In 2006 and 2007, the psychologist Gerd Gigerenzer gave a series of statistics
[04:02] seminars to practicing gynecologists, and he opened with the following example.
[04:06] A 50-year-old woman, no symptoms, participates in a routine mammography screening.
[04:12] She tests positive, is alarmed, and wants to know from you
[04:15] whether she has breast cancer for certain or what her chances are.
[04:18] Apart from the screening result, you know nothing else about this woman.
[04:22] In that seminar, the doctors were then told that the prevalence of
[04:26] breast cancer for women of this age is about 1%,
[04:29] and then to suppose that the test sensitivity is 90% and that its specificity was 91%.
[04:34] You might notice these are exactly the same numbers
[04:36] from the example that you and I just looked at.
[04:38] This is where I got them.
[04:39] So, having already thought it through, you and I know the answer.
[04:42] It's about 1 in 11.
[04:44] However, the doctors in this session were not primed with the suggestion to
[04:47] picture a concrete sample of a thousand individuals, the way that you and I had.
[04:52] All they saw were these numbers.
[04:54] They were then asked, how many women who test positive actually have breast cancer?
[04:58] What is the best answer?
[04:59] And they were presented with these four choices.
[05:01] In one of the sessions, over half the doctors present
[05:05] said that the correct answer was 9 in 10, which is way off.
[05:10] Only a fifth of them gave the correct answer, which is worse
[05:12] than what it would have been if everybody had randomly guessed.
[05:16] It might seem a little extreme to be calling this a paradox.
[05:19] I mean, it's just a fact.
[05:21] It's not something intrinsically self-contradictory.
[05:24] But, as these seminars with Gigerenzer show, people, including doctors,
[05:28] definitely find it counterintuitive that a test with high accuracy can give you such a
[05:33] low predictive value.
[05:35] We might call this a veridical paradox, which refers to facts that are provably true,
[05:40] but which nevertheless can feel false when phrased a certain way.
[05:44] It's sort of the softest form of a paradox, saying
[05:46] more about human psychology than about logic.
[05:49] The question is how we can combat this.
[05:53] Where we're going with this, by the way, is that I want you to be able
[05:57] to look at numbers like this and quickly estimate in your head that it
[06:00] means the predictive value of a positive test should be around 1 in 11.
[06:04] Or, if I changed things and asked, what if it
[06:07] was 10% of the population who had breast cancer?
[06:10] You should be able to quickly turn around and say
[06:12] that the final answer would be a little over 50%.
[06:15] Or, if I said imagine a really low prevalence,
[06:18] something like 0.1% of patients having cancer,
[06:21] you should again quickly estimate that the predictive value of the test is around 1 in
[06:25] 100, that 1 in 100 of those with positive test results in that case would have cancer.
[06:31] Or, let's say we go back to the 1% prevalence, but I make the test more accurate.
[06:35] I tell you to imagine the specificity is 99%.
[06:38] There, you should be able to relatively quickly
[06:41] estimate that the answer is a little less than 50%.
[06:44] The hope is that you're doing all of this with minimal calculations in your head.
[06:48] Now, the goals of quick calculations might feel very different from the goals of
[06:52] addressing whatever misconception underlies this paradox,
[06:54] but they actually go hand in hand.
[06:56] Let me show you what I mean.
[06:58] On the side of addressing misconceptions, what would you
[07:01] tell to the people in that seminar who answered 9 and 10?
[07:04] What fundamental misconception are they revealing?
[07:08] What I might tell them is that in much the same way that you shouldn't think
[07:11] of tests as telling you deterministically whether you have a disease,
[07:14] you shouldn't even think of them as telling you your chances of having a disease.
[07:19] Instead, the healthy view of what tests do is that they update your chances.
[07:26] In our example, before taking the test, a patient's
[07:28] chances of having cancer were 1 in 100.
[07:31] In Bayesian terms, we call this the prior probability.
[07:34] The effect of this test was to update that prior by almost an order of magnitude,
[07:39] up to around 1 in 11.
[07:41] The accuracy of a test is telling us about the strength of this updating.
[07:45] It's not telling us a final answer.
[07:47] What does this have to do with quick approximations?
[07:50] Well, a key number for those approximations is something called the Bayes factor,
[07:54] and the very act of defining this number serves to reinforce this
[07:58] central lesson about reframing what it is the tests do.
[08:02] You see, one of the things that makes test statistics so very confusing
[08:05] is that there are at least 4 numbers that you'll hear associated with them.
[08:08] For those with the disease, there's the sensitivity and the false negative rate,
[08:12] and then for those without, there's the specificity and the false positive rate,
[08:15] and none of these numbers actually tell you the thing you want to know.
[08:19] Luckily, if you want to interpret a positive test result,
[08:22] you can pull out just one number to focus on from all this.
[08:26] Take the sensitivity divided by the false positive rate.
[08:29] In other words, how much more likely are you to see
[08:31] the positive test result with cancer versus without?
[08:34] In our example, this number is 10.
[08:37] This is the Bayes factor, also sometimes called the likelihood ratio.
[08:43] A very handy rule of thumb is that to update a small prior,
[08:46] or at least to approximate the answer, you simply multiply it by the Bayes factor.
[08:50] So in our example, where the prior was 1 in 100,
[08:53] you would estimate that the final answer should be around 1 in 10,
[08:56] which is in fact slightly above the true correct answer.
[08:59] So based on this rule of thumb, if I asked you what would happen if the
[09:03] prior from our example was instead 1 in 1000, you could quickly estimate
[09:07] that the effect of the test should be to update those chances to around 1 in 100.
[09:12] And in fact, take a moment to check yourself by thinking through a sample population.
[09:16] In this case, you might picture 10,000 patients where only 10 of them really have cancer.
[09:22] And then based on that 90% sensitivity, we would
[09:24] expect 9 of those cancer cases to give true positives.
[09:29] And on the other side, a 91% specificity means that
[09:32] 9% of those without cancer are getting false positives.
[09:36] So we'd expect 9% of the remaining patients, which is around 900,
[09:40] to give false positive results.
[09:42] Here, with such a low prevalence, the false positives
[09:45] really do dominate the true positives.
[09:47] So the probability that a randomly chosen positive case from this population
[09:52] actually has cancer is only around 1%, just like the rule of thumb predicted.
[09:58] Now, this rule of thumb clearly cannot work for higher priors.
[10:02] For example, it would predict that a prior of
[10:05] 10% gets updated all the way to 100% certainty.
[10:08] But that can't be right.
[10:10] In fact, take a moment to think through what the answer should be,
[10:13] again, using a sample population.
[10:15] Maybe this time we picture 10 out of 100 having cancer.
[10:18] Again, based on the 90% sensitivity of the test,
[10:21] we'd expect 9 of those true cancer cases to get positive results.
[10:24] But what about the false positives?
[10:26] How many do we expect there?
[10:29] About 9% of the remaining 90.
[10:32] About 8.
[10:33] So, upon seeing a positive test result, it tells you that you're
[10:37] either one of these 9 true positives or one of the 8 false positives.
[10:41] So this means the chances are a little over 50%, roughly 9 out of 17, or 53%.
[10:48] At this point, having dared to dream that Bayesian updating could look
[10:51] as simple as multiplication, you might tear down your hopes and pragmatically
[10:54] acknowledge that sometimes life is just more complicated than that.
[10:59] Except it's not.
[11:01] This rule of thumb turns into a precise mathematical fact as long as we
[11:05] shift away from talking about probabilities to instead talking about odds.
[11:10] If you've ever heard someone talk about the chances of an event being 1 to 1 or 2 to 1,
[11:14] things like that, you already know about odds.
[11:17] With probability, we're taking the ratio of the number
[11:20] of positive cases out of all possible cases, right?
[11:23] Things like 1 in 5 or 1 in 10.
[11:25] With odds, what you do is take the ratio of all positive cases to all negative cases.
[11:31] You commonly see odds written with a colon to emphasize the distinction,
[11:34] but it's still just a fraction, just a number.
[11:37] So an event with a 50% probability would be described as having 1 to 1 odds.
[11:42] A 10% probability is the same as 1 to 9 odds.
[11:46] An 80% probability is the same as 4 to 1 odds.
[11:49] You get the point.
[11:51] It's the same information.
[11:52] It still describes the chances of a random event,
[11:55] but it's presented a little differently, like a different unit system.
[11:59] Probabilities are constrained between 0 and 1, with even chances sitting at 0.5.
[12:04] But odds range from 0 up to infinity, with even chances sitting at the number 1.
[12:11] The beauty here is that a completely accurate,
[12:14] not even approximating things way to frame Bayes' rule is to say,
[12:18] express your prior using odds, and then just multiply by the Bayes' factor.
[12:23] Think about what the prior odds are really saying.
[12:25] It's the number of people with cancer divided by the number without it.
[12:29] Here, let's just write that down as a normal fraction for a moment so we can multiply it.
[12:33] When you filter down just to those with positive test results,
[12:36] the number of people with cancer gets scaled down,
[12:39] scaled down by the probability of seeing a positive test result given
[12:43] that someone has cancer.
[12:45] And then similarly, the number of people without cancer also gets scaled down,
[12:49] this time by the probability of seeing a positive test result, but in that case.
[12:54] So the ratio between these two counts, the new odds upon seeing the test,
[12:58] looks just like the prior odds except multiplied by this term here,
[13:02] which is exactly the Bayes' factor.
[13:07] Look back at our example, where the Bayes' factor was 10.
[13:11] And as a reminder, this came from the 90% sensitivity
[13:14] divided by the 9% false positive rate.
[13:16] How much more likely are you to see a positive result with cancer versus without?
[13:21] If the prior is 1%, expressed as odds, this looks like 1 to 99.
[13:26] So by our rule, this gets updated to 10 to 99,
[13:29] which if you want you could convert back to a probability.
[13:33] It would be 10 divided by 10 plus 99, or about 1 in 11.
[13:38] If instead, the prior was 10%, which was the example that tripped up
[13:42] our rule of thumb earlier, expressed as odds, this looks like 1 to 9.
[13:46] By our simple rule, this gets updated to 10 to 9,
[13:49] which you can already read off pretty intuitively.
[13:52] It's a little above even chances, a little above 1 to 1.
[13:56] If you prefer, you can convert it back to a probability.
[13:59] You would write it as 10 out of 19, or about 53%.
[14:03] And indeed, that is what we already found by thinking
[14:05] things through with a sample population.
[14:08] Let's say we go back to the 1% prevalence, but I make the test more accurate.
[14:12] Now what if I told you to imagine that the false positive rate was only 1% instead of 9%?
[14:17] What that would mean is that our Bayes factor is 90 instead of 10.
[14:20] The test is doing more work for us.
[14:23] In this case, with the more accurate test, it gets updated to 90 to 99,
[14:27] which is a little less than even chances, something a little under 50%.
[14:31] To be more precise, you could make the conversion
[14:34] back to probability and work out that it's around 48%.
[14:37] But honestly, if you're just going for a gut feel, it's fine to stick with the odds.
[14:42] Do you see what I mean about how just defining this
[14:44] number helps to combat potential misconceptions?
[14:48] For anybody who's a little hasty in connecting test accuracy directly to your probability
[14:52] of having a disease, it's worth emphasizing that you could administer the same test with
[14:57] the same accuracy to multiple different patients who all get the same exact result,
[15:01] but if they're coming from different contexts,
[15:04] that result can mean wildly different things.
[15:06] However, the one thing that does stay constant in every case
[15:10] is the factor by which each patient's prior odds get updated.
[15:16] And by the way, this whole time we've been using the prevalence of the disease,
[15:20] which is the proportion of people in a population who have it,
[15:23] as a substitute for the prior, the probability of having it before you see a test.
[15:27] However, that's not necessarily the case.
[15:29] If there are other known factors, things like symptoms,
[15:32] or in the case of a contagious disease, things like known contacts,
[15:35] those also factor into the prior, and they could potentially make a huge difference.
[15:40] As another side note, so far we've only talked about positive test results,
[15:44] but way more often you would be seeing a negative test result.
[15:48] The logic there is completely the same, but the base
[15:50] factor that you compute is going to look different.
[15:52] Instead, you look at the probability of seeing this negative
[15:55] test result with the disease versus without the disease.
[15:58] So in our cancer example, this would have been the 10% false
[16:02] negative rate divided by the 91% specificity, or about 1 in 9.
[16:07] In other words, seeing a negative test result in that example
[16:11] would reduce your prior odds by about an order of magnitude.
[16:15] When you write it all out as a formula, here's how it looks.
[16:18] It says your odds of having a disease given a test result equals your
[16:22] odds before taking the test, the prior odds, times the base factor.
[16:26] Now let's contrast this with the usual way Bayes' rule is written,
[16:30] which is a bit more complicated.
[16:33] In case you haven't seen it before, it's essentially just what we were
[16:36] doing with sample populations, but you wrap it all up symbolically.
[16:39] Remember how every time we were counting the number of true positives and
[16:42] then dividing it by the sum of the true positives and the false positives?
[16:46] We do just that, except instead of talking about absolute amounts,
[16:50] we talk of each term as a proportion.
[16:52] So the proportion of true positives in the population comes
[16:55] from the prior probability of having the disease multiplied
[16:58] by the probability of seeing a positive test result in that case.
[17:03] Then we copy that term down again into the denominator,
[17:05] and then the proportion of false positives comes from the prior
[17:09] probability of not having the disease times the probability of a positive
[17:13] test in that case.
[17:15] If you want, you could also write this down with words instead of symbols,
[17:18] if terms like sensitivity and false positive rate are more comfortable.
[17:21] And this is one of those formulas where once you say it out loud it seems like a bit
[17:24] much, but it really is no different from what we were doing with sample populations.
[17:29] If you wanted to make the whole thing look simpler,
[17:31] you often see this entire denominator written just as the probability of seeing a
[17:35] positive test result, overall.
[17:37] While that does make for a really elegant little expression,
[17:40] if you intend to use this for calculations, it's a little disingenuous,
[17:44] because in practice, every single time you do this you need to break
[17:47] down that denominator into two separate parts, breaking down the cases.
[17:51] So taking this more honest representation of it,
[17:53] let's compare our two versions of Bayes' rule.
[17:56] And again, maybe it looks nicer if we use the words sensitivity and false positive rate.
[18:00] If nothing else, it helps emphasize which parts of the
[18:03] formula are coming from statistics about the test accuracy.
[18:05] I mean, this actually emphasizes one thing I really like about the framing with
[18:09] odds and a Bayes' factor, which is that it cleanly factors out the parts that
[18:12] have to do with the prior and the parts that have to do with the test accuracy.
[18:16] But over in the usual formula, all of those are very intermingled together.
[18:20] And this has a very practical benefit.
[18:22] It's really nice if you want to swap out different priors and easily see their effects.
[18:26] This is what we were doing earlier.
[18:28] But with the other formula, to do that, you have to recompute everything each time.
[18:32] You can't leverage a precomputed Bayes' factor the same way.
[18:35] The odds framing also makes things really nice if you want to do
[18:38] multiple different Bayesian updates based on multiple pieces of evidence.
[18:42] For example, let's say you took not one test, but two.
[18:45] Or you wanted to think about how the presence of symptoms plays into it.
[18:49] For each piece of new evidence you see, you always ask the question,
[18:52] how much more likely would you be to see that with the disease versus without the disease?
[18:57] Each answer to that question gives you a new Bayes' factor,
[19:00] a new thing that you multiply by your odds.
[19:02] Beyond just making calculations easier, there's something I really like about
[19:06] attaching a number to test accuracy that doesn't even look like a probability.
[19:10] I mean, if you hear that a test has, for example,
[19:13] a 9% false positive rate, that's just such a disastrously ambiguous phrase.
[19:17] It's so easy to misinterpret it to mean there's a
[19:20] 9% chance that your positive test result is false.
[19:23] But imagine if instead the number that we heard tacked on to test
[19:26] results was that the Bayes' factor for a positive test result is, say, 10.
[19:30] There's no room to confuse that for your probability of having a disease.
[19:34] The entire framing of what a Bayes' factor is,
[19:36] is that it's something that acts on a prior.
[19:39] It forces your hand to acknowledge the prior as something that's separate entirely,
[19:43] and highly necessary to drawing any conclusion.
[19:47] All that said, the usual formula is definitely not without its merits.
[19:51] If you view it not simply as something to plug numbers into,
[19:53] but as an encapsulation of the sample population idea that we've been using throughout,
[19:58] you could very easily argue that that's actually much better for your intuition.
[20:02] After all, it's what we were routinely falling back on in order to check
[20:05] ourselves that the Bayes' factor computation even made sense in the first place.
[20:11] Like any design decision, there is no clear-cut objective best here.
[20:15] But it's almost certainly the case that giving serious consideration
[20:18] to that question will lead you to a better understanding of Bayes' rule.
[20:30] Also, since we're on the topic of kind of paradoxical things,
[20:32] a friend of mine, Matt Cook, recently wrote a book all about paradoxes.
[20:37] I actually contributed a small chapter to it with thoughts
[20:39] on the question of whether math is invented or discovered.
[20:42] And the book as a whole is this really nice connection of thought-provoking
[20:45] paradoxical things ranging from philosophy to math and physics.
[20:48] You can, of course, find all the details in the description. 352 00:20:58,100 --&gt; 00:20:51,040 .
