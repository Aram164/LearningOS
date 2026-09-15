---
video_id: zeJD6dqJ5lo
url: https://www.youtube.com/watch?v=zeJD6dqJ5lo
title: But what is the Central Limit Theorem?
channel: 3Blue1Brown
duration: 31:14
language: en
unit: L08
status: OK
---

[00:00] This is a Galton board.
[00:02] Maybe you've seen one before, it's a popular demonstration of how,
[00:05] even when a single event is chaotic and random, with an effectively unknowable outcome,
[00:10] it's still possible to make precise statements about a large number of events,
[00:14] namely how the relative proportions for many different outcomes are distributed.
[00:20] More specifically, the Galton board illustrates one of the most prominent
[00:24] distributions in all probability, known as the normal distribution,
[00:27] more colloquially known as a bell curve, and also called a Gaussian distribution.
[00:32] There's a very specific function to describe this distribution, it's very pretty,
[00:36] we'll get into it later, but right now I just want to emphasize how the normal
[00:40] distribution is, as the name suggests, very common,
[00:42] it shows up in a lot of seemingly unrelated contexts.
[00:46] If you were to take a large number of people who sit in a similar demographic
[00:49] and plot their heights, those heights tend to follow a normal distribution.
[00:53] If you look at a large swath of very big natural numbers,
[00:56] and you ask how many distinct prime factors does each one of those numbers have,
[01:01] the answers will very closely track with a certain normal distribution.
[01:05] Now our topic for today is one of the crown jewels in all of probability theory,
[01:09] it's one of the key facts that explains why this distribution is as common as it is,
[01:14] known as the central limit theorem.
[01:16] This lesson is meant to go back to the basics,
[01:18] giving you the fundamentals on what the central limit theorem is saying,
[01:22] what normal distributions are, and I want to assume minimal background.
[01:25] We're going to go decently deep into it, but after this I'd still like to
[01:29] go deeper and explain why the theorem is true,
[01:31] why the function underlying the normal distribution has the very specific
[01:36] form that it does, why that formula has a pi in it, and, most fun,
[01:39] why those last two facts are actually more related than a lot of traditional
[01:44] explanations would suggest.
[01:46] That second lesson is also meant to be the follow-on to the convolutions
[01:50] video that I promised, so there's a lot of interrelated topics here.
[01:53] But right now, back to the fundamentals, I'd like to kick
[01:56] things off with an overly simplified model of the Galton board.
[02:00] In this model we will assume that each ball falls directly onto a certain central peg,
[02:05] and that it has a 50-50 probability of bouncing to the left or to the right,
[02:09] and we'll think of each of those outcomes as either adding one or subtracting one from
[02:13] its position.
[02:14] Once one of those is chosen, we make the highly unrealistic assumption that it
[02:18] happens to land dead on in the middle of the peg adjacent below it,
[02:22] where again it'll be faced with the same 50-50 choice of bouncing to the left or
[02:26] to the right.
[02:27] For the one I'm showing on screen, there are five different rows of pegs,
[02:31] so our little hopping ball makes five different random choices between plus one
[02:35] and minus one, and we can think of its final position as basically being the
[02:38] sum of all of those different numbers, which in this case happens to be one,
[02:42] and we might label all of the different buckets with the sum that they represent,
[02:46] as we repeat this we're looking at different possible sums for those five random numbers.
[02:53] And for those of you who are inclined to complain that this is a highly unrealistic model
[02:57] for the true Galton board, let me emphasize the goal right now is not to accurately model
[03:01] physics, the goal is to give a simple example to illustrate the central limit theorem,
[03:05] and for that, idealized though this might be, it actually gives us a really good example.
[03:10] If we let many different balls fall, making yet another unrealistic
[03:13] assumption that they don't influence each other, as if they're all ghosts,
[03:17] then the number of balls that fall into each different bucket gives
[03:20] us some loose sense for how likely each one of those buckets is.
[03:23] In this example, the numbers are simple enough that it's not too hard to
[03:26] explicitly calculate what the probability is for falling into each bucket.
[03:30] If you do want to think that through, you'll find it very reminiscent of Pascal's
[03:34] triangle, but the neat thing about our theorem is how far it goes beyond the simple
[03:37] examples.
[03:38] So to start off at least, rather than making explicit calculations,
[03:41] let's just simulate things by running a large number of samples and letting the total
[03:45] number of results in each different outcome give us some sense for what that distribution
[03:49] looks like.
[03:50] As I said, the one on screen has five rows, so each
[03:53] sum that we're considering includes only five numbers.
[03:56] The basic idea of the central limit theorem is that if you increase the size of that sum,
[04:01] for example here would mean increasing the number of rows of pegs for each
[04:06] ball to bounce off, then the distribution that describes where that sum
[04:10] is going to fall looks more and more like a bell curve.
[04:15] Here, it's actually worth taking a moment to write down that general idea.
[04:19] The setup is that we have a random variable, and that's basically shorthand for
[04:23] a random process where each outcome of that process is associated with some number.
[04:28] We'll call that random number x.
[04:29] For example, each bounce off the peg is a random process modeled with two outcomes.
[04:34] Those outcomes are associated with the numbers negative one and positive one.
[04:38] Another example of a random variable would be rolling a die,
[04:41] where you have six different outcomes, each one associated with a number.
[04:45] What we're doing is taking multiple different
[04:47] samples of that variable and adding them all together.
[04:50] On our Galton board, that looks like letting the ball bounce off multiple
[04:54] different pegs on its way down to the bottom, and in the case of a die,
[04:57] you might imagine rolling many different dice and adding up the results.
[05:01] The claim of the central limit theorem is that as you let the size of that sum
[05:05] get bigger and bigger, then the distribution of that sum,
[05:08] how likely it is to fall into different possible values,
[05:11] will look more and more like a bell curve.
[05:15] That's it, that is the general idea.
[05:17] Over the course of this lesson, our job is to make that statement more quantitative.
[05:22] We're going to put some numbers to it, put some formulas to it,
[05:24] show how you can use it to make predictions.
[05:27] For example, here's the kind of question I want
[05:29] you to be able to answer by the end of this video.
[05:32] Suppose you rolled a die 100 times and you added together the results.
[05:36] Could you find a range of values such that you're
[05:39] 95% sure that the sum will fall within that range?
[05:42] Or maybe I should say find the smallest possible range of values such that this is true.
[05:47] The neat thing is you'll be able to answer this question
[05:49] whether it's a fair die or if it's a weighted die.
[05:53] Now let me say at the top that this theorem has three different assumptions
[05:56] that go into it, three things that have to be true before the theorem follows.
[06:00] And I'm actually not going to tell you what they are until the very end of the video.
[06:04] Instead I want you to keep your eye out and see if you can notice
[06:07] and maybe predict what those three assumptions are going to be.
[06:10] As a next step, to better illustrate just how general this theorem is,
[06:13] I want to run a couple more simulations for you focused on the dice example.
[06:20] Usually if you think of rolling a die you think of the six outcomes as
[06:24] being equally probable, but the theorem actually doesn't care about that.
[06:27] We could start with a weighted die, something with a non-trivial
[06:31] distribution across the outcomes, and the core idea still holds.
[06:35] For the simulation what I'll do is take some distribution
[06:37] like this one that is skewed towards lower values.
[06:40] I'm going to take 10 distinct samples from that distribution and
[06:43] then I'll record the sum of that sample on the plot on the bottom.
[06:48] Then I'm going to do this many many different times, always with a sum of size 10,
[06:52] but keep track of where those sums ended up to give us a sense of the distribution.
[06:59] And in fact let me rescale the y direction to give
[07:02] us room to run an even larger number of samples.
[07:05] And I'll let it go all the way up to a couple thousand,
[07:07] and as it does you'll notice that the shape that starts to emerge looks like a bell curve.
[07:12] Maybe if you squint your eyes you can see it skews a tiny bit to the left,
[07:16] but it's neat that something so symmetric emerged from a starting point that was so
[07:20] asymmetric.
[07:21] To better illustrate what the central limit theorem is all about,
[07:24] let me run four of these simulations in parallel,
[07:27] where on the upper left I'm doing it where we're only adding two dice at a time,
[07:31] on the upper right we're doing it where we're adding five dice at a time,
[07:34] the lower left is the one that we just saw adding 10 dice at a time,
[07:38] and then we'll do another one with a bigger sum, 15 at a time.
[07:42] Notice how on the upper left when we're just adding two dice,
[07:45] the resulting distribution doesn't really look like a bell curve,
[07:48] it looks a lot more reminiscent of the one we started with, skewed towards the left.
[07:52] But as we allow for more and more dice in each sum,
[07:55] the resulting shape that comes up in these distributions looks more and more symmetric.
[07:59] It has the lump in the middle and fade towards the tail's shape of a bell curve.
[08:07] And let me emphasize again, you can start with any different distribution.
[08:10] Here I'll run it again, but where most of the probability is tied up
[08:13] in the numbers 1 and 6, with very low probability for the mid values.
[08:18] Despite completely changing the distribution for an individual roll of the die,
[08:22] it's still the case that a bell curve shape will emerge as we consider the different sums.
[08:27] Illustrating things with a simulation like this is very fun,
[08:30] and it's kind of neat to see order emerge from chaos,
[08:33] but it also feels a little imprecise.
[08:35] Like in this case, when I cut off the simulation at 3000 samples,
[08:38] even though it kind of looks like a bell curve,
[08:40] the different buckets seem pretty spiky, and you might wonder,
[08:43] is it supposed to look that way, or is that just an artifact of the
[08:47] randomness in the simulation?
[08:49] And if it is, how many samples do we need before we can be sure that
[08:52] what we're looking at is representative of the true distribution?
[08:59] Instead moving forward, let's get a little more theoretical and show
[09:02] the precise shape these distributions will take on in the long run.
[09:06] The easiest case to make this calculation is if we have a uniform distribution,
[09:10] where each possible face of the die has an equal probability, 1 6th.
[09:13] For example, if you then want to know how likely different sums are for a pair of dice,
[09:18] it's essentially a counting game, where you count up how many distinct
[09:21] pairs take on the same sum, which in the diagram I've drawn,
[09:24] you can conveniently think about by going through all the different diagonals.
[09:31] Since each such pair has an equal chance of showing up,
[09:34] 1 in 36, all you have to do is count the sizes of these buckets.
[09:38] That gives us a definitive shape for the distribution describing a sum of two dice,
[09:42] and if we were to play the same game with all possible triplets,
[09:45] the resulting distribution would look like this.
[09:48] Now what's more challenging, but a lot more interesting,
[09:51] is to ask what happens if we have a non-uniform distribution for that single die.
[09:55] We actually talked all about this in the last video.
[09:58] You do essentially the same thing, you go through all
[10:00] the distinct pairs of dice which add up to the same value.
[10:03] It's just that instead of counting those pairs,
[10:06] for each pair you multiply the two probabilities of each particular face coming up,
[10:10] and then you add all those together.
[10:13] The computation that does this for all possible sums has a fancy name,
[10:16] it's called a convolution, but it's essentially just the weighted version of
[10:20] the counting game that anyone who's played with a pair of dice already finds familiar.
[10:25] For our purposes in this lesson, I'll have the computer calculate all that,
[10:28] simply display the results for you, and invite you to observe certain patterns,
[10:33] but under the hood, this is what's going on.
[10:36] So just to be crystal clear on what's being represented here,
[10:39] if you imagine sampling two different values from that top distribution,
[10:43] the one describing a single die, and adding them together,
[10:46] then the second distribution I'm drawing represents how likely you are to
[10:50] see various different sums.
[10:52] Likewise, if you imagine sampling three distinct values from that top distribution,
[10:57] and adding them together, the next plot represents the probabilities
[11:00] for various different sums in that case.
[11:03] So if I compute what the distributions for these sums look like for larger and larger
[11:08] sums, well you know what I'm going to say, it looks more and more like a bell curve.
[11:13] But before we get to that, I want you to make a couple more simple observations.
[11:17] For example, these distributions seem to be wandering to the right,
[11:20] and also they seem to be getting more spread out, and a little bit more flat.
[11:25] You cannot describe the central limit theorem quantitatively
[11:27] without taking into account both of those effects,
[11:30] which in turn requires describing the mean and the standard deviation.
[11:33] Maybe you're already familiar with those, but I want to make minimal assumptions here,
[11:37] and it never hurts to review, so let's quickly go over both of those.
[11:43] The mean of a distribution, often denoted with the Greek letter mu,
[11:47] is a way of capturing the center of mass for that distribution.
[11:51] It's calculated as the expected value of our random variable,
[11:54] which is a way of saying you go through all of the different possible outcomes,
[11:58] and you multiply the probability of that outcome times the value of the variable.
[12:03] If higher values are more probable, that weighted sum is going to be bigger.
[12:06] If lower values are more probable, that weighted sum is going to be smaller.
[12:10] A little more interesting is if you want to measure how spread out this distribution is,
[12:14] because there's multiple different ways you might do it.
[12:18] One of them is called the variance.
[12:20] The idea there is to look at the difference between each possible value and the mean,
[12:25] square that difference, and ask for its expected value.
[12:28] The idea is that whether your value is below or above the mean,
[12:31] when you square that difference, you get a positive number,
[12:34] and the larger the difference, the bigger that number.
[12:37] Squaring it like this turns out to make the math much much nicer than if we did
[12:41] something like an absolute value, but the downside is that it's hard to think about
[12:45] this as a distance in our diagram because the units are off,
[12:48] kind of like the units here are square units, whereas a distance in our diagram would
[12:52] be a kind of linear unit.
[12:53] So another way to measure spread is what's called the standard deviation,
[12:57] which is the square root of this value.
[12:59] That can be interpreted much more reasonably as a distance on our diagram,
[13:03] and it's commonly denoted with the Greek letter sigma,
[13:06] so you know m for mean as for standard deviation, but both in Greek.
[13:11] Looking back at our sequence of distributions,
[13:13] let's talk about the mean and standard deviation.
[13:16] If we call the mean of the initial distribution mu,
[13:19] which for the one illustrated happens to be 2.24,
[13:21] hopefully it won't be too surprising if I tell you that the mean
[13:25] of the next one is 2 times mu.
[13:27] That is, you roll a pair of dice, you want to know the expected value of the sum,
[13:30] it's two times the expected value for a single die.
[13:33] Similarly, the expected value for our sum of size 3 is 3 times mu, and so on and so forth.
[13:39] The mean just marches steadily on to the right,
[13:41] which is why our distributions seem to be drifting off in that direction.
[13:45] A little more challenging, but very important,
[13:47] is to describe how the standard deviation changes.
[13:50] The key fact here is that if you have two different random variables,
[13:53] then the variance for the sum of those variables is the same
[13:56] as just adding together the original two variances.
[13:59] This is one of those facts that you can just compute when you unpack all the definitions.
[14:03] There are a couple nice intuitions for why it's true.
[14:06] My tentative plan is to just actually make a series about probability and
[14:10] talk about things like intuitions underlying variance and its cousins there.
[14:14] But right now, the main thing I want you to highlight is how it's the variance that adds,
[14:18] it's not the standard deviation that adds.
[14:20] So, critically, if you were to take n different realizations of the same random
[14:24] variable and ask what the sum looks like, the variance of sum is n times the
[14:29] variance of your original variable, meaning the standard deviation,
[14:33] the square root of all this, is the square root of n times the original standard
[14:37] deviation.
[14:39] For example, back in our sequence of distributions,
[14:41] if we label the standard deviation of our initial one with sigma,
[14:45] then the next standard deviation is going to be the square root of 2 times sigma,
[14:49] and after that it looks like the square root of 3 times sigma, and so on and so forth.
[14:53] This, like I said, is very important.
[14:56] It means that even though our distributions are getting spread out,
[14:59] they're not spreading out all that quickly, they only do so
[15:01] in proportion to the square root of the size of the sum.
[15:04] As we prepare to make a more quantitative description of the central limit theorem,
[15:08] the core intuition I want you to keep in your head is that we'll basically realign
[15:12] all of these distributions so that their means line up together,
[15:15] and then rescale them so that all of the standard deviations are just going to be
[15:19] equal to one.
[15:21] And when we do that, the shape that results gets closer and closer to a certain universal
[15:25] shape, described with an elegant little function that we'll unpack in just a moment.
[15:30] And let me say one more time, the real magic here is how we could have started with
[15:34] any distribution, describing a single roll of the die, and if we play the same game,
[15:39] considering what the distributions for the many different sums look like,
[15:43] and we realign them so that the means line up,
[15:45] and we rescale them so that the standard deviations are all one,
[15:48] we still approach that same universal shape, which is kind of mind-boggling.
[15:54] And now, my friends, is probably as good a time as any
[15:57] to finally get into the formula for a normal distribution.
[16:01] And the way I'd like to do this is to basically peel
[16:03] back all the layers and build it up one piece at a time.
[16:06] The function e to the x, or anything to the x, describes exponential growth,
[16:10] and if you make that exponent negative, which flips around the graph horizontally,
[16:15] you might think of it as describing exponential decay.
[16:18] To make this decay in both directions, you could do something to make sure the
[16:21] exponent is always negative and growing, like taking the negative absolute value.
[16:25] That would give us this kind of awkward sharp point in the middle,
[16:29] but if instead you make that exponent the negative square of x,
[16:32] you get a smoother version of the same thing, which decays in both directions.
[16:36] This gives us the basic bell curve shape.
[16:38] Now if you throw a constant in front of that x,
[16:41] and you scale that constant up and down, it lets you stretch and
[16:44] squish the graph horizontally, allowing you to describe narrow and wider bell curves.
[16:49] And a quick thing I'd like to point out here is that based on the
[16:52] rules of exponentiation, as we tweak around that constant c,
[16:55] you could also think about it as simply changing the base of the exponentiation.
[17:00] And in that sense, the number e is not really all that special for our formula.
[17:04] We could replace it with any other positive constant,
[17:06] and you'll get the same family of curves as we tweak that constant.
[17:11] Make it a 2, same family of curves.
[17:13] Make it a 3, same family of curves.
[17:15] The reason we use e is that it gives that constant a very readable meaning.
[17:20] Or rather, if we reconfigure things a little bit so that the exponent looks
[17:24] like negative 1 half times x divided by a certain constant,
[17:27] which we'll suggestively call sigma squared, then once we turn this into a
[17:31] probability distribution, that constant sigma will be the standard deviation
[17:36] of that distribution.
[17:37] And that's very nice.
[17:38] But before we can interpret this as a probability distribution,
[17:42] we need the area under the curve to be 1.
[17:44] And the reason for that is how the curve is interpreted.
[17:47] Unlike discrete distributions, when it comes to something continuous,
[17:50] you don't ask about the probability of a particular point.
[17:53] Instead, you ask for the probability that a value falls between two different values.
[17:58] And what the curve is telling you is that that probability
[18:02] equals the area under the curve between those two values.
[18:06] There's a whole other video about this, they're called probability density functions.
[18:09] The main point right now is that the area under the entire curve represents
[18:13] the probability that something happens, that some number comes up.
[18:17] That should be 1, which is why we want the area under this to be 1.
[18:21] As it stands with the basic bell curve shape of e to the negative x squared,
[18:24] the area is not 1, it's actually the square root of pi.
[18:28] I know, right?
[18:29] What is pi doing here?
[18:30] What does this have to do with circles?
[18:32] Like I said at the start, I'd love to talk all about that in the next video.
[18:35] But if you can spare your excitement, for our purposes right now,
[18:38] all it means is that we should divide this function by the square root of pi,
[18:41] and it gives us the area we want.
[18:43] Throwing back in the constants we had earlier, the one half and the sigma,
[18:47] the effect there is to stretch out the graph by a factor of sigma times the square
[18:51] root of 2.
[18:52] So we also need to divide out by that in order to make sure it has an area of 1,
[18:56] and combining those fractions, the factor out front looks like
[18:59] 1 divided by sigma times the square root of 2 pi.
[19:02] This, finally, is a valid probability distribution.
[19:06] As we tweak that value sigma, resulting in narrower and wider curves,
[19:10] that constant in the front always guarantees that the area equals 1.
[19:15] The special case where sigma equals 1 has a specific name,
[19:18] we call it the standard normal distribution, which plays an especially important role
[19:23] for you and me in this lesson.
[19:25] And all possible normal distributions are not only parameterized with this value sigma,
[19:29] but we also subtract off another constant mu from the variable x,
[19:33] and this essentially just lets you slide the graph left and right so
[19:37] that you can prescribe the mean of this distribution.
[19:40] So in short, we have two parameters, one describing the mean,
[19:43] one describing the standard deviation, and they're all tied together in this big formula
[19:48] involving an e and a pi.
[19:49] Now that all of that is on the table, let's look back again at the idea of starting with
[19:54] some random variable and asking what the distributions for sums of that variable look
[19:59] like.
[20:00] As we've already gone over, when you increase the size of that sum,
[20:03] the resulting distribution will shift according to a growing mean,
[20:06] and it slowly spreads out according to a growing standard deviation.
[20:10] And putting some actual formulas to it, if we know the mean of our underlying
[20:14] random variable, we call it mu, and we also know its standard deviation,
[20:18] and we call it sigma, then the mean for the sum on the bottom will be mu times
[20:22] the size of the sum, and the standard deviation will be sigma times the square
[20:26] root of that size.
[20:28] So now, if we want to claim that this looks more and more like a bell curve,
[20:31] and a bell curve is only described by two different parameters,
[20:34] the mean and the standard deviation, you know what to do.
[20:37] You could plug those two values into the formula, and it gives you a highly explicit,
[20:42] albeit kind of complicated, formula for a curve that should closely fit our distribution.
[20:48] But there's another way we can describe it that's a little more
[20:51] elegant and lends itself to a very fun visual that we can build up to.
[20:55] Instead of focusing on the sum of all of these random variables,
[20:58] let's modify this expression a little bit, where what we'll do is we'll look
[21:02] at the mean that we expect that sum to take, and we subtract it off so that
[21:06] our new expression has a mean of zero, and then we're going to look at the
[21:10] standard deviation we expect of our sum, and divide out by that,
[21:13] which basically just rescales the units so that the standard deviation of our
[21:17] expression will equal one.
[21:19] This might seem like a more complicated expression,
[21:21] but it actually has a highly readable meaning.
[21:24] It's essentially saying how many standard deviations away from the mean is this sum?
[21:30] For example, this bar here corresponds to a certain value that you might find when you
[21:34] roll 10 dice and you add them all up, and its position a little above negative one is
[21:39] telling you that that value is a little bit less than one standard deviation lower than
[21:43] the mean.
[21:45] Also, by the way, in anticipation for the animation I'm trying to build to here,
[21:48] the way I'm representing things on that lower plot is that the area of each one of
[21:52] these bars is telling us the probability of the corresponding value rather than the
[21:56] height.
[21:57] You might think of the y-axis as representing
[21:59] not probability but a kind of probability density.
[22:02] The reason for this is to set the stage so that it aligns with the way we
[22:05] interpret continuous distributions, where the probability of falling between
[22:09] a range of values is equal to an area under a curve between those values.
[22:13] In particular, the area of all the bars together is going to be one.
[22:18] Now, with all of that in place, let's have a little fun.
[22:21] Let me start by rolling things back so that the distribution on the bottom represents
[22:25] a relatively small sum, like adding together only three such random variables.
[22:29] Notice what happens as I change the distribution we start with.
[22:32] As it changes, the distribution on the bottom completely changes its shape.
[22:36] It's very dependent on what we started with.
[22:40] If we let the size of our sum get a little bit bigger, say going up to 10,
[22:44] and as I change the distribution for x, it largely stays looking like a bell curve,
[22:48] but I can find some distributions that get it to change shape.
[22:52] For example, the really lopsided one where almost all the probability
[22:55] is in the numbers 1 or 6 results in this kind of spiky bell curve.
[22:59] And if you'll recall, earlier on I actually showed this in the form of a simulation.
[23:04] Though if you were wondering whether that spikiness was an artifact of the randomness
[23:08] or reflected the true distribution, turns out it reflects the true distribution.
[23:12] In this case, 10 is not a large enough sum for the central limit theorem to kick in.
[23:16] But if instead I let that sum grow and I consider adding 50 different values,
[23:20] which is actually not that big, then no matter how I change the distribution for our
[23:25] underlying random variable, it has essentially no effect on the shape of the plot on
[23:30] the bottom.
[23:31] No matter where we start, all of the information and nuance for the
[23:34] distribution of x gets washed away, and we tend towards this single
[23:38] universal shape described by a very elegant function for the standard
[23:42] normal distribution, 1 over square root of 2 pi times e to the negative x squared over 2.
[23:47] This, this right here is what the central limit theorem is all about.
[23:51] Almost nothing you can do to this initial distribution changes the shape we tend towards.
[23:59] Now, the more theoretically minded among you might still be
[24:02] wondering what is the actual theorem, like what's the mathematical
[24:05] statement that could be proved or disproved that we're claiming here.
[24:09] If you want a nice formal statement, here's how it might go.
[24:12] Consider this value where we're summing up n different instantiations of our variable,
[24:16] but tweaked and tuned so that its mean and standard deviation are 1,
[24:20] again meaning you can read it as asking how many standard deviations away from the
[24:24] mean is the sum.
[24:25] Then the actual rigorous no-jokes-this-time statement of the central limit theorem
[24:30] is that if you consider the probability that this value falls between two given real
[24:35] numbers, a and b, and you consider the limit of that probability as the size of your
[24:40] sum goes to infinity, then that limit is equal to a certain integral,
[24:44] which basically describes the area under a standard normal distribution between those
[24:49] two values.
[24:51] Again, there are three underlying assumptions that I have yet to tell you,
[24:55] but other than those, in all of its gory detail,
[24:57] this right here is the central limit theorem.
[25:04] All of that is a bit theoretical, so it might be helpful to bring things
[25:07] back down to earth and turn back to the concrete example that I mentioned at the start,
[25:12] where you imagine rolling a die 100 times, and let's assume it's a fair
[25:15] die for this example, and you add together the results.
[25:18] The challenge for you is to find a range of values such that
[25:22] you're 95% sure that the sum will fall within this range.
[25:27] For questions like this, there's a handy rule of thumb about normal distributions,
[25:31] which is that about 68% of your values are going to fall within one standard
[25:35] deviation of the mean, 95% of your values, the thing we care about,
[25:39] fall within two standard deviations of the mean,
[25:42] and a whopping 99.7% of your values will fall within three standard
[25:45] deviations of the mean.
[25:47] It's a rule of thumb that's commonly memorized
[25:49] by people who do a lot of probability and stats.
[25:52] Naturally, this gives us what we need for our example,
[25:55] and let me go ahead and draw out what this would look like,
[25:58] where I'll show the distribution for a fair die up at the top,
[26:01] and the distribution for a sum of 100 such dice on the bottom,
[26:04] which by now as you know looks like a certain normal distribution.
[26:07] Step 1 with a problem like this is to find the mean of your initial distribution,
[26:12] which in this case will look like 1 6th times 1 plus 1 6th times 2 on and on and on,
[26:17] and works out to be 3.5.
[26:19] We also need the standard deviation, which requires calculating the variance,
[26:23] which as you know involves adding all the squares of the differences between the
[26:27] values and the means, and it works out to be 2.92,
[26:30] square root of that comes out to be 1.71.
[26:32] Those are the only two numbers we need, and I will invite you
[26:35] again to reflect on how magical it is that those are the only
[26:38] two numbers you need to completely understand the bottom distribution.
[26:42] Its mean will be 100 times mu, which is 350, and its standard deviation
[26:47] will be the square root of 100 times sigma, so 10 times sigma, 17.1.
[26:53] Remembering our handy rule of thumb, we're looking for values two standard
[26:57] deviations away from the mean, and when you subtract 2 sigma from mean,
[27:01] you end up with about 316, and when you add 2 sigma you end up with 384.
[27:07] There you go, that gives us the answer.
[27:11] Okay, I promised to wrap things up shortly, but while we're on this example,
[27:14] there's one more question that's worth your time to ponder.
[27:18] Instead of just asking about the sum of 100 die rolls,
[27:21] let's say I had you divide that number by 100,
[27:23] which basically means all the numbers in our diagram in the bottom get divided by 100.
[27:28] Take a moment to interpret what this all would be saying then.
[27:32] The expression essentially tells you the empirical average for 100 different die rolls,
[27:37] and that interval we found is now telling you what range you are
[27:40] expecting to see for that empirical average.
[27:44] In other words, you might expect it to be around 3.5,
[27:47] that's the expected value for a die roll, but what's much less obvious and what
[27:51] the central limit theorem lets you compute is how close to that expected value
[27:54] you'll reasonably find yourself.
[27:57] In particular, it's worth your time to take a moment mulling over
[28:00] what the standard deviation for this empirical average is,
[28:03] and what happens to it as you look at a bigger and bigger sample of die rolls.
[28:12] Lastly, but probably most importantly, let's talk
[28:15] about the assumptions that go into this theorem.
[28:18] The first one is that all of these variables that
[28:20] we're adding up are independent from each other.
[28:22] The outcome of one process doesn't influence the outcome of any other process.
[28:27] The second is that all of these variables are drawn from the same distribution.
[28:31] Both of these have been implicitly assumed with our dice example.
[28:34] We've been treating the outcome of each die roll as independent from the outcome
[28:38] of all the others, and we're assuming that each die follows the same distribution.
[28:42] Sometimes in the literature you'll see these two assumptions lumped
[28:46] together under the initials IID for independent and identically distributed.
[28:50] One situation where these assumptions are decidedly not true would be the Galton board.
[28:55] I mean, think about it.
[28:56] Is it the case that the way a ball bounces off of one of the pegs
[29:00] is independent from how it's going to bounce off the next peg?
[29:03] Absolutely not.
[29:04] Depending on the last bounce, it's coming in with a completely different trajectory.
[29:08] And is it the case that the distribution of possible outcomes
[29:11] off of each peg are the same for each peg that it hits?
[29:15] Again, almost certainly not.
[29:16] Maybe it hits one peg glancing to the left, meaning the outcomes are hugely
[29:20] skewed in that direction, and then hits the next one glancing to the right.
[29:25] When I made all those simplifying assumptions in the opening example,
[29:29] it wasn't just to make this easier to think about.
[29:31] It's also that those assumptions were necessary for this
[29:34] to actually be an example of the central limit theorem.
[29:38] Nevertheless, it seems to be true that for the real Galton board,
[29:41] despite violating both of these, a normal distribution does kind of come about?
[29:46] Part of the reason might be that there are generalizations of the theorem beyond
[29:49] the scope of this video that relax these assumptions, especially the second one.
[29:54] But I do want to caution you against the fact that many times people seem to assume that
[29:58] a variable is normally distributed, even when there's no actual justification to do so.
[30:04] The third assumption is actually fairly subtle.
[30:06] It's that the variance we've been computing for these variables is finite.
[30:10] This was never an issue for the dice example because
[30:13] there were only six possible outcomes.
[30:15] But in certain situations where you have an infinite set of outcomes,
[30:18] when you go to compute the variance, the sum ends up diverging off to infinity.
[30:23] These can be perfectly valid probability distributions, and they do come up in practice.
[30:27] But in those situations, as you consider adding many different
[30:30] instantiations of that variable and letting that sum approach infinity,
[30:34] even if the first two assumptions hold, it is very much a possibility
[30:37] that the thing you tend towards is not actually a normal distribution.
[30:42] If you've understood everything up to this point,
[30:44] you now have a very strong foundation in what the central limit theorem is all about.
[30:48] And next up, I'd like to explain why it is that this particular function is the
[30:52] thing that we tend towards, and why it has a pi in it, what it has to do with circles.
[31:11] Thank you.
