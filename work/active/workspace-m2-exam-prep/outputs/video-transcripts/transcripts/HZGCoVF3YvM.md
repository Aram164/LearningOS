---
video_id: HZGCoVF3YvM
url: https://www.youtube.com/watch?v=HZGCoVF3YvM
title: Bayes theorem, the geometry of changing beliefs
channel: 3Blue1Brown
duration: 15:11
language: en
unit: L01
status: OK
---

[00:00] The goal is for you to come away from this video understanding one
[00:03] of the most important formulas in all of probability, Bayes' theorem.
[00:07] This formula is central to scientific discovery,
[00:10] it's a core tool in machine learning and AI, and it's even been used for treasure
[00:14] hunting, when in the 1980s a small team led by Tommy Thompson,
[00:18] and I'm not making up that name, used Bayesian search tactics to help uncover a
[00:23] ship that had sunk a century and a half earlier,
[00:25] and the ship was carrying what in today's terms amounts to $700 million worth of gold.
[00:31] So it's a formula worth understanding, but of course there
[00:34] are multiple different levels of possible understanding.
[00:37] At the simplest there's just knowing what each one of the parts means,
[00:40] so that you can plug in numbers.
[00:42] Then there's understanding why it's true, and later I'm going to show you a
[00:46] certain diagram that's helpful for rediscovering this formula on the fly as needed.
[00:51] But maybe the most important level is being able to recognize when you need to use it.
[00:55] And with the goal of gaining a deeper understanding,
[00:58] you and I are going to tackle these in reverse order.
[01:01] So before dissecting the formula or explaining the visual that makes it obvious,
[01:04] I'd like to tell you about a man named Steve.
[01:07] Listen carefully now.
[01:12] Steve is very shy and withdrawn, invariably helpful but
[01:15] with very little interest in people or the world of reality.
[01:19] A meek and tidy soul, he has a need for order and structure, and a passion for detail.
[01:24] Which of the following do you find more likely?
[01:27] Steve is a librarian, or Steve is a farmer?
[01:31] Some of you may recognize this as an example from a study
[01:34] conducted by the two psychologists Daniel Kahneman and Amos Tversky.
[01:38] Their work was a big deal, it won a Nobel Prize,
[01:40] and it's been popularized many times over in books like Kahneman's Thinking Fast and
[01:44] Slow, or Michael Lewis's The Undoing Project.
[01:47] What they researched was human judgments, with a frequent focus on when these
[01:51] judgments irrationally contradict what the laws of probability suggest they should be.
[01:56] The example with Steve, our maybe-librarian-maybe-farmer,
[01:59] illustrates one specific type of irrationality,
[02:02] or maybe I should say alleged irrationality, there are people who debate the
[02:06] conclusion here, but more on all of that later on.
[02:09] According to Kahneman and Tversky, after people are given this description
[02:13] of Steve as a meek and tidy soul, most say he's more likely to be a librarian.
[02:18] After all, these traits line up better with the
[02:20] stereotypical view of a librarian than a farmer.
[02:24] And according to Kahneman and Tversky, this is irrational.
[02:27] The point is not whether people hold correct or biased views about the
[02:31] personalities of librarians and farmers, it's that almost nobody thinks to
[02:35] incorporate information about the ratio of farmers to librarians in their judgments.
[02:40] In their paper, Kahneman and Tversky said that in the US that ratio is about 20 to 1.
[02:45] The numbers I could find today put that much higher,
[02:48] but let's stick with the 20 to 1 number, since it's a little easier to illustrate
[02:52] and proves the point as well.
[02:54] To be clear, anyone who has asked this question is not expected to have perfect
[02:58] information about the actual statistics of farmers and librarians and their personality
[03:02] traits.
[03:03] But the question is whether people even think to consider
[03:06] that ratio enough to at least make a rough estimate.
[03:10] Rationality is not about knowing facts, it's about recognizing which facts are relevant.
[03:15] Now if you do think to make that estimate, there's a pretty
[03:18] simple way to reason about the question, which, spoiler alert,
[03:21] involves all of the essential reasoning behind Bayes' theorem.
[03:24] You might start by picturing a representative sample of farmers and librarians,
[03:29] say 200 farmers and 10 librarians.
[03:31] Then when you hear of this meek and tidy soul description,
[03:35] let's say that your gut instinct is that 40% of librarians would fit that description,
[03:39] and 10% of farmers would.
[03:42] If those are your estimates, it would mean that from your sample you would expect
[03:45] about 4 librarians to fit the description, and about 20 farmers to fit that description.
[03:51] So the probability that a random person among those who
[03:55] fit this description is a librarian is 4 out of 24, or 16.7%.
[04:00] So even if you think that a librarian is 4 times as likely as a farmer to fit this
[04:04] description, that's not enough to overcome the fact that there are way more farmers.
[04:09] The upshot, and this is the key mantra underlying Bayes' theorem,
[04:13] is that new evidence does not completely determine your beliefs in a vacuum.
[04:17] It should update prior beliefs.
[04:21] If this line of reasoning makes sense to you, the way that
[04:23] seeing evidence restricts the space of possibilities,
[04:26] and the ratio you need to consider after that, then congratulations!
[04:30] You understand the heart of Bayes' theorem.
[04:32] Maybe the numbers you would estimate would be a little different,
[04:35] but what matters is how you fit the numbers together to update your beliefs based
[04:39] on evidence.
[04:42] Now understanding one example is one thing, but see if you can take a minute
[04:46] to generalize everything we just did and write it all down as a formula.
[04:52] The general situation where Bayes' theorem is relevant is when you have some hypothesis,
[04:57] like Steve is a librarian, and you see some new evidence,
[05:00] say this verbal description of Steve as a meek and tidy soul,
[05:04] and you want to know the probability that your hypothesis holds given that
[05:08] the evidence is true.
[05:10] In the standard notation, this vertical bar means given that,
[05:14] as in we're restricting our view only to the possibilities where the evidence holds.
[05:20] Now remember the first relevant number we used,
[05:22] it was the probability that the hypothesis holds before considering
[05:26] any of that new evidence.
[05:27] In our example, that was 1 out of 21, and it came from considering
[05:31] the ratio of librarians to farmers in the general population.
[05:35] This number is known as the prior.
[05:38] After that, we need to consider the proportion of librarians that fit this description,
[05:42] the probability that we would see the evidence given that the hypothesis is true.
[05:48] Again, when you see this vertical bar, it means we're talking about
[05:51] some proportion of a limited part of the total space of possibilities.
[05:55] In this case, that limited part is the left side, where the hypothesis holds.
[05:59] In the context of Bayes' theorem, this value also has a special name,
[06:03] it's called the likelihood.
[06:05] Similarly, you need to know how much of the other side of the space includes the
[06:09] evidence, the probability of seeing the evidence given that the hypothesis isn't true.
[06:14] This funny little elbow symbol is commonly used in probability to mean not.
[06:19] So with the notation in place, remember what our final answer was,
[06:23] the probability that our librarian hypothesis is true given the evidence is the total
[06:28] number of librarians fitting the evidence, 4, divided by the total number of people
[06:33] fitting the evidence, 24.
[06:35] But where did that 4 come from?
[06:37] Well, it's the total number of people times the prior probability of being a librarian,
[06:42] giving us the 10 total librarians, times the probability that
[06:46] one of those fits the evidence.
[06:49] That same number shows up again in the denominator, but we need to add in the rest,
[06:53] the total number of people times the proportion who are not librarians,
[06:57] times the proportion of those who fit the evidence, which in our example gives 20.
[07:03] Now notice the total number of people here, 210, that gets cancelled out,
[07:06] and of course it should, that was just an arbitrary choice made for the sake of
[07:10] illustration.
[07:11] This leaves us finally with a more abstract representation purely
[07:15] in terms of probabilities, and this, my friends, is Bayes' theorem.
[07:20] More often, you see this denominator written simply as P of E,
[07:24] the total probability of seeing the evidence, which in our example would be
[07:29] the 24 out of 210.
[07:31] But in practice, to calculate it, you almost always have to break it down
[07:35] into the case where the hypothesis is true, and the one where it isn't.
[07:40] Capping things off with one final bit of jargon, this answer is called the posterior,
[07:44] it's your belief about the hypothesis after seeing the evidence.
[07:50] Writing it out abstractly might seem more complicated than just
[07:53] thinking through the example directly with a representative sample.
[07:56] And yeah, it is.
[07:59] Keep in mind though, the value of a formula like this is that it
[08:02] lets you quantify and systematize the idea of changing beliefs.
[08:06] Scientists use this formula when they're analyzing the extent
[08:10] to which new data validates or invalidates their models.
[08:12] Programmers will sometimes use it in building artificial intelligence,
[08:16] where at times you want to explicitly and numerically model a machine's belief.
[08:21] And honestly, just for the way you view yourself and your own
[08:24] opinions and what it takes for your mind to change,
[08:26] Bayes' theorem has a way of reframing how you even think about thought itself.
[08:32] Putting a formula to it can also be more important
[08:34] as the examples get more and more intricate.
[08:37] However you end up writing it, I actually encourage you not to try
[08:40] memorizing the formula, but to instead draw out this diagram as needed.
[08:45] It's sort of a distilled version of thinking with a representative sample,
[08:48] where we think with areas instead of counts, which is more flexible and easier to sketch
[08:53] on the fly.
[08:54] Rather than bringing to mind some specific number of examples,
[08:57] like 210, think of the space of all possibilities as a 1x1 square.
[09:02] Then any event occupies some subset of this space,
[09:05] and the probability of that event can be thought about as the area of that subset.
[09:11] For example, I like to think of the hypothesis as living
[09:14] in the left part of the square with a width of p of h.
[09:18] I recognize I'm being a bit repetitive, but when you see evidence,
[09:22] the space of possibilities gets restricted, right?
[09:24] And the crucial part is that restriction might not be even between
[09:29] the left and the right, so the new probability for the hypothesis
[09:33] is the proportion it occupies in this restricted wonky shape.
[09:37] Now, if you happen to think that a farmer is just as likely to fit the evidence
[09:41] as a librarian, then the proportion doesn't change, which should make sense, right?
[09:46] Irrelevant evidence doesn't change your beliefs.
[09:48] But when these likelihoods are very different from each other,
[09:51] that's when your belief changes a lot.
[09:55] Bayes' theorem spells out what that proportion is,
[09:58] and if you want you can read it geometrically.
[10:00] Something like p of h times p of e given h, the probability of both
[10:04] the hypothesis and the evidence occurring together,
[10:08] is the width times the height of this little left rectangle, the area of that region.
[10:14] Alright, this is probably a good time to take a step back and consider a few of the
[10:18] broader takeaways about how to make probability more intuitive,
[10:21] beyond just Bayes' theorem.
[10:23] First off, notice how the trick of thinking about a representative sample with some
[10:28] specific number of people, like our 210 librarians and farmers, was really helpful.
[10:32] There's actually another Kahneman and Tversky result which is all about this,
[10:36] and it's interesting enough to interject here.
[10:38] They did this experiment that was similar to the one with Steve,
[10:41] but where people were given the following description of a fictitious woman named Linda.
[10:46] Linda is 31 years old, single, outspoken, and very bright.
[10:51] She majored in philosophy.
[10:52] As a student she was deeply concerned with issues of discrimination and social justice,
[10:56] and also participated in the anti-nuclear demonstrations.
[11:00] After seeing this, people were asked what's more likely, 1.
[11:04] That Linda is a bank teller, or 2.
[11:06] That Linda is a bank teller and is active in the feminist movement.
[11:11] 85%, 85% of participants said that the latter is more likely than the former,
[11:16] even though the set of bank tellers who are active in the feminist
[11:20] movement is a subset of the set of bank tellers.
[11:23] It has to be smaller.
[11:25] So that's interesting enough, but what's fascinating is that there's a simple
[11:29] way that you can rephrase the question that dropped this error from 85% to 0.
[11:34] Instead, if participants were told that there are 100 people who fit this description,
[11:39] and then they're asked to estimate how many of those 100 are bank tellers,
[11:43] and how many of them are bank tellers who are active in the feminist movement,
[11:47] nobody makes the error.
[11:48] Everybody correctly assigns a higher number to the first option than to the second.
[11:54] It's weird, somehow phrases like 40 out of 100 kick our intuitions
[11:59] into gear much more effectively than 40%, much less 0.4,
[12:02] and much less abstractly referencing the idea of something being more or less likely.
[12:09] That said, representative samples don't easily capture the continuous
[12:12] nature of probability, so turning to area is a nice alternative not just
[12:16] because of the continuity, but also because it's way easier to sketch
[12:20] out when you're sitting there pencil and paper puzzling over some problem.
[12:25] You see, people often think about probability as being the study of uncertainty,
[12:29] and that is of course how it's applied in science, but the actual math of probability,
[12:34] where all the formulas come from, is just the math of proportions,
[12:37] and in that context turning to geometry is exceedingly helpful.
[12:44] I mean, take a look at Bayes' theorem as a statement about proportions,
[12:47] whether that's proportions of people, of areas, whatever.
[12:51] Once you digest what it's saying, it's actually kind of obvious.
[12:55] Both sides tell you to look at the cases where the evidence is true,
[12:58] and then to consider the proportion of those cases where the hypothesis is also true.
[13:03] That's it, that's all it's saying, the right hand side just spells out how to compute it.
[13:07] What's noteworthy is that such a straightforward fact about proportions
[13:11] can become hugely significant for science, for artificial intelligence,
[13:14] and really any situation where you want to quantify belief.
[13:18] I hope to give you a better glimpse of that as we get into more examples.
[13:22] But before more examples, we have a little bit of unfinished business with Steve.
[13:26] As I mentioned, some psychologists debate Kahneman and Tversky's conclusion,
[13:30] that the rational thing to do is to bring to mind the ratio of farmers to librarians.
[13:35] They complain that the context is ambiguous.
[13:37] I mean, who is Steve, exactly?
[13:39] Should you expect that he's a randomly sampled American?
[13:43] Or would you be better to assume that he's a friend
[13:45] of the two psychologists interrogating you?
[13:47] Or maybe that he's someone you're personally likely to know?
[13:50] This assumption determines the prior.
[13:52] I for one run into way more librarians in a given month than I do farmers.
[13:57] And needless to say, the probability of a librarian or farmer
[14:00] fitting this description is highly open to interpretation.
[14:04] For our purposes, understanding the math, what I want to emphasize is that
[14:08] any question worth debating here can be pictured in the context of the diagram.
[14:13] Questions about the context shift around the prior,
[14:15] and questions about the personalities and stereotypes shift around the
[14:19] relevant likelihoods.
[14:21] All that said, whether or not you buy this particular experiment,
[14:24] the ultimate point that evidence should not determine beliefs, but update them,
[14:29] is worth tattooing in your brain.
[14:31] I'm in no position to say whether this does or
[14:34] does not run against natural human instinct.
[14:36] We'll leave that to the psychologists.
[14:38] What's more interesting to me is how we can reprogram our intuition to authentically
[14:43] reflect the implications of math, and bringing to mind the right image can often do just
[14:47] that.
