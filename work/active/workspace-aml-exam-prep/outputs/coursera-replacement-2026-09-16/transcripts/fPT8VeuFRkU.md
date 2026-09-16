---
video_id: fPT8VeuFRkU
url: https://www.youtube.com/watch?v=fPT8VeuFRkU
title: Logistic regression 3: The decision boundary and weight vector
channel: Herman Kamper
duration: 20:32
language: en
unit: L05
status: OK
---

[00:00] in this video we're going to take a bit
[00:02] in this video we're going to take a bit of a deeper look
[00:03] of a deeper look at the decision boundary in binary
[00:06] at the decision boundary in binary logistic regression
[00:07] logistic regression we're specifically going to look at the
[00:09] we're specifically going to look at the relationship between the decision
[00:11] relationship between the decision boundary
[00:12] boundary and the parameter vector what we
[00:14] and the parameter vector what we sometimes just call the weight vector
[00:16] sometimes just call the weight vector as a little spoiler what we will see is
[00:19] as a little spoiler what we will see is that the weight vector is always orthogonal
[00:22] the weight vector is always orthogonal to the decision boundary
[00:24] to the decision boundary if we look at the weight vector in the
[00:26] if we look at the weight vector in the feature space
[00:27] feature space let's take a closer look at the decision
[00:30] let's take a closer look at the decision boundary
[00:31] boundary so the decision boundary are the values
[00:33] so the decision boundary are the values
[00:34] so the decision boundary are the values of x for which we're perfectly unsure about
[00:37] for which we're perfectly unsure about whether
[00:38] whether the input is in the positive or the
[00:40] the input is in the positive or the negative class
[00:42] negative class stated more formally these are the
[00:44] stated more formally these are the values of
[00:45] values of x for which the output of a model is at
[00:48] x for which the output of a model is at 50 percent
[00:49] 50 percent a 0.5 for the probability of belonging
[00:52] a 0.5 for the probability of belonging to the positive class
[00:54] to the positive class and that implies that it's also
[00:55] and that implies that it's also probability of 50
[00:57] probability of 50 of x belonging to the negative clause
[01:00] of x belonging to the negative clause now if we're using
[01:01] now if we're using binary logistic regression then our
[01:04] binary logistic regression then our model is defined as the sigmoid
[01:06] model is defined as the sigmoid of w transpose times x
[01:09] of w transpose times x and given the definition of the sigmoid
[01:11] and given the definition of the sigmoid you can go and convince yourself
[01:13] you can go and convince yourself that the values of x where if we take
[01:16] that the values of x where if we take the sigmoid of w transpose
[01:18] the sigmoid of w transpose x and get a value of 0.5 those values of
[01:22] x and get a value of 0.5 those values of x would be the values where w transpose
[01:25] x would be the values where w transpose times x is equal to zero this is one case
[01:29] x is equal to zero this is one case where it might actually be easier to
[01:31] where it might actually be easier to explicitly include the bias term
[01:34] explicitly include the bias term so here in this first statement here
[01:36] so here in this first statement here here we
[01:37] here we still use this little hack where we
[01:39] still use this little hack where we pretend that the first dimension of x
[01:42] pretend that the first dimension of x is equal to one and what we do now is
[01:44] is equal to one and what we do now is we're going to rather
[01:46] we're going to rather write out explicitly the bias term so
[01:48] write out explicitly the bias term so here we've got
[01:50] here we've got the sigmoid of w0 plus w
[01:53] the sigmoid of w0 plus w transpose times x and here this x
[01:56] transpose times x and here this x doesn't include the first dimension as
[01:58] doesn't include the first dimension as one the first dimension of x would just
[02:00] one the first dimension of x would just be whatever that features value is
[02:03] be whatever that features value is now if we do this then this equation
[02:07] now if we do this then this equation here w zero plus w transpose times x
[02:10] w zero plus w transpose times x that where that equation gives us values
[02:13] that where that equation gives us values of zero
[02:14] of zero that is our decision boundary to get
[02:17] that is our decision boundary to get more of an intuition for
[02:18] more of an intuition for what the decision boundary looks like
[02:20] what the decision boundary looks like we're just going to look at an example
[02:22] we're just going to look at an example in two dimensions
[02:24] in two dimensions and what i've done here is i've just
[02:26] and what i've done here is i've just written out
[02:27] written out a number of steps that we're going to
[02:29] a number of steps that we're going to follow and then we're going to see what
[02:30] follow and then we're going to see what the decision boundary looks like
[02:32] the decision boundary looks like in the feature space in this
[02:34] in the feature space in this two-dimensional case
[02:35] two-dimensional case
[02:36] two-dimensional case so maybe you can just pause here and
[02:37] so maybe you can just pause here and actually try and do these steps on your
[02:40] actually try and do these steps on your own before looking at the rest of the video
[02:43] before looking at the rest of the video cool i hope you made a solid attempt to
[02:45] cool i hope you made a solid attempt to do that
[02:46] do that so the values of x1 and x2
[02:49] so the values of x1 and x2 where if we plug in those values of x1
[02:52] where if we plug in those values of x1 and x2
[02:53] and x2 into this equation and we get 0 those
[02:55] into this equation and we get 0 those are the values of
[02:56] are the values of x where we're on the decision boundary
[02:59] x where we're on the decision boundary
[03:00] x where we're on the decision boundary so the first step here says sketch this
[03:02] so the first step here says sketch this line w zero plus
[03:03] line w zero plus
[03:04] line w zero plus w one x plus w two x two equal to zero
[03:07] w one x plus w two x two equal to zero in the x one x two plane in other words
[03:10] in the x one x two plane in other words in our feature plane
[03:12] in our feature plane so if we say that this is the first
[03:14] so if we say that this is the first feature x one
[03:15] feature x one and this is the feature x x2 then this
[03:18] and this is the feature x x2 then this equation here
[03:19] equation here defines a straight line when x1 is equal
[03:23] defines a straight line when x1 is equal to 0
[03:24] to 0 when x1 is equal to 0 then x2 will be
[03:27] when x1 is equal to 0 then x2 will be
[03:28] equal to negative w0 divided by w2 and similarly
[03:32] negative w0 divided by w2 and similarly when
[03:33] when x2 is equal to 0 then x1 will be
[03:37] x2 is equal to 0 then x1 will be negative w0 divided by
[03:40] negative w0 divided by w1 and this is a straight line so we're
[03:43] w1 and this is a straight line so we're just going to connect those points
[03:45] just going to connect those points i'm going to struggle to do it in a
[03:47] i'm going to struggle to do it in a pretty way but let's try
[03:49] pretty way but let's try so after about 10 tries i'm happy with
[03:51] so after about 10 tries i'm happy with that line now that line is supposed to
[03:53] that line now that line is supposed to be straight
[03:54] be straight and that defines the equation if you
[03:56] and that defines the equation if you want to write it in that y is equal to
[03:58] want to write it in that y is equal to mx plus c
[03:59] mx plus c kind of form then this is the equation
[04:01] kind of form then this is the equation x2
[04:02] x2 is equal to negative w1
[04:05] is equal to negative w1 over w2 x1
[04:09] over w2 x1 minus w0 divided by
[04:12] minus w0 divided by w2 okay so that's step one done
[04:15] w2 okay so that's step one done now the next step sketch the vector w1
[04:20] now the next step sketch the vector w1 w2 in this same plane in the x1
[04:23] w2 in this same plane in the x1
[04:24] w2 in this same plane in the x1 x2 plane so if we're in the xy plane
[04:26] x2 plane so if we're in the xy plane then this value here
[04:28] then this value here that will just be w1 and this value here
[04:33] that will just be w1 and this value here that will just be w2 step 3
[04:36] that will just be w2 step 3 redraw the line in one this line that we
[04:39] redraw the line in one this line that we drew here
[04:40] drew here but to pretend that w zero is equal to
[04:44] but to pretend that w zero is equal to zero so if we do that if w zero is equal
[04:47] zero so if we do that if w zero is equal to zero then
[04:48] to zero then that term falls away and it's just
[04:50] that term falls away and it's just basically this line but it's moved to
[04:52] basically this line but it's moved to the origin
[04:53] the origin so let's draw that in now prove that the
[04:55] so let's draw that in now prove that the line in three
[04:56] line in three this thing is orthogonal to the line in
[04:58] this thing is orthogonal to the line in two in other words to this vector here
[05:02] two in other words to this vector here let's say we move w1 down on the x2 axis
[05:05] let's say we move w1 down on the x2 axis so we're w1 down on the x2 axis
[05:08] so we're w1 down on the x2 axis so we just go this much down here so
[05:11] so we just go this much down here so that gives us a point somewhere there
[05:14] that gives us a point somewhere there let's say we're somewhere there okay so
[05:17] let's say we're somewhere there okay so this point here is
[05:18] this point here is negative w1 then on the x1
[05:22] negative w1 then on the x1 axis because the gradient of this line
[05:25] axis because the gradient of this line is w1 over w2
[05:27] is w1 over w2 then on the x1 axis this value here
[05:30] then on the x1 axis this value here that would just that point there would
[05:32] that would just that point there would be w2
[05:34] be w2 so that means we've got a triangle here
[05:37] so that means we've got a triangle here this length here is w1 and this length
[05:40] this length here is w1 and this length is w2
[05:41] is w2 and here we've got the same triangle
[05:44] and here we've got the same triangle this length here is w1 and this length here
[05:47] length here is w1 and this length here is w2
[05:48] is w2 so that means we can basically do some
[05:53] so that means we can basically do some great zero mathematics here so that
[05:55] great zero mathematics here so that angle there you can convince yourself
[05:57] angle there you can convince yourself would be the same as that
[05:59] would be the same as that angle there and this angle here
[06:02] angle there and this angle here because these two triangles are the same
[06:05] because these two triangles are the same be the same as that
[06:06] be the same as that angle there this angle would be 90
[06:08] angle there this angle would be 90 degrees
[06:09] degrees and this angle would also be 90 degrees
[06:12] and this angle would also be 90 degrees and that means that the because
[06:16] and that means that the because the sum of the angles inside need to be
[06:18] the sum of the angles inside need to be 180 you've got 90 it means that the sum
[06:20] 180 you've got 90 it means that the sum of these two
[06:21] of these two would be 90 which basically means that
[06:25] would be 90 which basically means that this angle here is 90 degrees and that
[06:27] this angle here is 90 degrees and that means
[06:28] means that this line and this line they're
[06:31] that this line and this line they're orthogonal to one another
[06:33] orthogonal to one another okay now why go through all of those
[06:35] okay now why go through all of those steps because that means that
[06:37] steps because that means that if we draw the vector w1w2
[06:40] if we draw the vector w1w2 in the x-space this vector here then
[06:43] in the x-space this vector here then that vector if
[06:44] that vector if you think about extending it here that
[06:46] you think about extending it here that vector will be orthogonal to our
[06:49] vector will be orthogonal to our decision boundary
[06:50] decision boundary and that's the whole point of of this
[06:53] and that's the whole point of of this little slide here
[06:54] little slide here is to illustrate that by just looking at
[06:57] is to illustrate that by just looking at this vector w1 w2
[07:00] this vector w1 w2 if i just give you those values then you
[07:02] if i just give you those values then you can already
[07:04] can already very quickly tell me in the x space
[07:07] very quickly tell me in the x space in the x1 x2 space how would my decision
[07:10] in the x1 x2 space how would my decision boundary
[07:11] boundary be kind of tilted now what's the effect
[07:14] be kind of tilted now what's the effect of w0 what if we bring
[07:16] of w0 what if we bring in w0 let's just think about the
[07:18] in w0 let's just think about the decision boundary here
[07:20] decision boundary here if we make w 0 smaller or bigger
[07:23] if we make w 0 smaller or bigger it's not going to change the gradient of
[07:25] it's not going to change the gradient of this line but it is going to move the
[07:27] this line but it is going to move the whole thing up or down the non-biased terms in the
[07:30] up or down the non-biased terms in the weight vector w
[07:31] weight vector w that tells us how our decision boundary
[07:34] that tells us how our decision boundary is tilted the gradient of the decision
[07:36] is tilted the gradient of the decision boundary while the bias term w0
[07:39] boundary while the bias term w0
[07:40] boundary while the bias term w0 tells us the offset of a decision
[07:41] tells us the offset of a decision
[07:42] tells us the offset of a decision boundary
[07:43] boundary we can extend this idea to higher
[07:45] we can extend this idea to higher dimensions
[07:47] dimensions so let's first just ignore the bias term
[07:49] so let's first just ignore the bias term then the decision boundary is given by
[07:51] then the decision boundary is given by this equation where here we've got our
[07:53] this equation where here we've got our first feature multiplied by the first
[07:55] first feature multiplied by the first weight second feature second weight and
[07:57] weight second feature second weight and so on up to the capital d
[07:59] so on up to the capital d feature multiplied by the d th weight
[08:02] feature multiplied by the d th weight and you can summarize that equation
[08:03] and you can summarize that equation using w
[08:04] using w transpose times x is equal to zero okay
[08:07] transpose times x is equal to zero okay that's the decision boundary
[08:09] that's the decision boundary and if we think about w as this vector
[08:12] and if we think about w as this vector in this high dimensional
[08:13] in this high dimensional
[08:14] in this high dimensional feature space x then the x vectors on
[08:17] feature space x then the x vectors on the decision boundary in other words the
[08:18] the decision boundary in other words the x vectors for which this statement is
[08:20] x vectors for which this statement is true
[08:21] true will all be orthogonal to w because
[08:25] will all be orthogonal to w because their dot product is zero this thing is
[08:27] their dot product is zero this thing is just exactly the same as saying that
[08:29] just exactly the same as saying that
[08:30] just exactly the same as saying that w dot x and from the definition of your
[08:34] w dot x and from the definition of your black mathematics course you know that
[08:36] black mathematics course you know that this when this holds then it says
[08:38] this when this holds then it says then this means that w and x are
[08:41] then this means that w and x are orthogonal to one another
[08:42] orthogonal to one another in a high dimensional space we can add
[08:45] in a high dimensional space we can add the bias term back in so now we say okay
[08:47] bias term back in so now we say okay let's let's have a w0
[08:49] let's let's have a w0 we put that big in and that has the
[08:52] we put that big in and that has the effect of offsetting the decision
[08:54] effect of offsetting the decision boundary in the x space so the whole point of
[08:57] in the x space so the whole point of these first two slides
[08:59] these first two slides are to convince you that the w vector
[09:02] are to convince you that the w vector here
[09:03] here that is orthogonal to the decision
[09:05] that is orthogonal to the decision boundary
[09:06] boundary so let's use that insight that the
[09:09] so let's use that insight that the weight vector w
[09:10] weight vector w is orthogonal to our decision boundary
[09:13] is orthogonal to our decision boundary to get a little bit more insight into
[09:14] to get a little bit more insight into what gradient descent does
[09:16] what gradient descent does when you're using it to optimize a
[09:18] when you're using it to optimize a binary logistic regression model
[09:21] binary logistic regression model so in one of the previous videos we saw
[09:23] so in one of the previous videos we saw
[09:24] so in one of the previous videos we saw that the partial derivative of the
[09:26] that the partial derivative of the negative log likelihood the loss that
[09:28] negative log likelihood the loss that we're using
[09:29] we're using to optimize this model with respect to
[09:31] to optimize this model with respect to
[09:32] to optimize this model with respect to the weight vector is given by
[09:34] the weight vector is given by this equation here and if we're going to
[09:36] this equation here and if we're going to use gradient
[09:37] use gradient descent to optimize this loss then what
[09:40] descent to optimize this loss then what we're going to do is we're going to take
[09:41] we're going to do is we're going to take the current value of the parameter
[09:43] the current value of the parameter vector and then we're going to subtract
[09:46] vector and then we're going to subtract the learning rate
[09:47] the learning rate times the partial derivative and we're
[09:49] times the partial derivative and we're going to set that
[09:51] going to set that to the new value of w and we're going to
[09:53] to the new value of w and we're going to keep on
[09:54] keep on doing this so let's just simplify this a
[09:57] doing this so let's just simplify this a little bit
[09:58] little bit and look at an example in two dimensions
[10:01] and look at an example in two dimensions the one simplification we will make is
[10:03] the one simplification we will make is that we just have
[10:04] that we just have one training item a single x in coming
[10:07] one training item a single x in coming in so we don't have a summation over
[10:09] in so we don't have a summation over multiple training items and then the
[10:11] multiple training items and then the other
[10:12] other simplifying assumption we will make is
[10:14] simplifying assumption we will make is we'll just pretend for now that we don't
[10:16] we'll just pretend for now that we don't have a bias term w0
[10:18] have a bias term w0 so all our data maybe you can think
[10:20] so all our data maybe you can think about it like this all the data is
[10:22] about it like this all the data is basically
[10:23] basically centered around zero so we don't have
[10:25] centered around zero so we don't have any bias
[10:26] any bias so let's say that this is our current
[10:28] so let's say that this is our current decision boundary
[10:29] decision boundary here and that our current
[10:33] here and that our current parameter vector our weight vector is
[10:35] parameter vector our weight vector is pointing in this direction which of
[10:37] pointing in this direction which of course will be orthogonal
[10:38] course will be orthogonal to the decision boundary and now we
[10:40] to the decision boundary and now we observe a single
[10:42] observe a single training example here with a positive
[10:45] training example here with a positive label
[10:46] label now actually the current decision
[10:48] now actually the current decision boundary is super bad because
[10:50] boundary is super bad because uh the design boundary and i didn't say
[10:52] uh the design boundary and i didn't say this in the previous slide
[10:54] this in the previous slide but and you can convince yourself of
[10:55] but and you can convince yourself of
[10:56] but and you can convince yourself of this it always points in the direction
[10:57] this it always points in the direction
[10:58] this it always points in the direction of the positive clauses so according to
[10:59] of the positive clauses so according to the model at the moment
[11:01] the model at the moment this is all positive and this is all
[11:03] this is all positive and this is all negative
[11:04] negative and now we observe a positive training
[11:06] and now we observe a positive training point here
[11:07] point here
[11:08] point here so the decision boundary is pretty bad
[11:10] so the decision boundary is pretty bad but let's see what gradient the saint
[11:12] but let's see what gradient the saint does for this single point what will happen
[11:16] for this single point what will happen now is that
[11:17] now is that our new w new w
[11:20] our new w new w will be equal to the old w
[11:23] will be equal to the old w and then we going to substitute in this
[11:26] and then we going to substitute in this loss here into this equation here just
[11:28] loss here into this equation here just for a single point
[11:29] for a single point so here we've got a negative and here
[11:31] so here we've got a negative and here we've got a negative so here we've got
[11:33] we've got a negative so here we've got plus the learning rate times
[11:37] plus the learning rate times y n our label which is positive it's 1
[11:40] y n our label which is positive it's 1 minus the sigmoid of w and this will now
[11:44] minus the sigmoid of w and this will now be w old transpose times
[11:48] old transpose times x n this is our update
[11:52] x n this is our update so what we're going to do is we're going
[11:53] so what we're going to do is we're going to take the old vector and then we're
[11:55] to take the old vector and then we're going to add
[11:56] going to add this thing here now this is just some
[11:59] this thing here now this is just some scalar value
[12:00] scalar value let's look at it in a in a second and
[12:03] let's look at it in a in a second and here we've got some vector so we're
[12:05] here we've got some vector so we're going to add a vector to w
[12:07] going to add a vector to w which is some scalar times xn
[12:10] which is some scalar times xn so what does the scalar times xn look
[12:12] so what does the scalar times xn look like this vector is in the same
[12:15] like this vector is in the same direction as xn but is weighted in some way so that
[12:19] xn but is weighted in some way so that thing is parallel to the blue line
[12:21] thing is parallel to the blue line this line here is parallel to this line
[12:23] this line here is parallel to this line and this is the vector
[12:25] and this is the vector that we're adding to w old so our new w
[12:29] that we're adding to w old so our new w will be let's make it in red around here
[12:32] will be let's make it in red around here so that would be w new so what just
[12:36] so that would be w new so what just happened
[12:37] happened originally we had a very bad w
[12:40] originally we had a very bad w old right because we're observing a
[12:43] old right because we're observing a single training point here
[12:46] single training point here which is in the positive clause but all
[12:47] which is in the positive clause but all the positive stuff at the moment is here
[12:50] the positive stuff at the moment is here and then after the uptick we've got a w
[12:52] and then after the uptick we've got a w lying around here
[12:54] lying around here and that this resulting decision
[12:56] and that this resulting decision boundary right would be
[12:57] boundary right would be lying somewhere here which already makes
[13:00] lying somewhere here which already makes a better prediction on
[13:01] a better prediction on x a and if you keep on doing this then
[13:04] x a and if you keep on doing this then this rate vector will keep on rotating
[13:07] this rate vector will keep on rotating until it points if we just have a single
[13:10] until it points if we just have a single training example it will point perfectly
[13:12] training example it will point perfectly in the direction of x n but otherwise if we've got more
[13:15] x n but otherwise if we've got more training examples then it will basically
[13:17] training examples then it will basically point in the direction so that
[13:19] point in the direction so that intuitively
[13:20] intuitively most of the positive labels will be on
[13:22] most of the positive labels will be on the positive side
[13:23] the positive side
[13:24] the positive side there's one more thing to note on this
[13:25] there's one more thing to note on this slide let's just for a second forget
[13:27] slide let's just for a second forget about the figure here
[13:29] about the figure here and just focus on this equation let's
[13:32] and just focus on this equation let's say the model output for this
[13:34] say the model output for this particular training input is very good
[13:37] particular training input is very good in other words for this particular
[13:39] in other words for this particular training input we want the model to
[13:40] training input we want the model to output a 1
[13:41] output a 1 and let's say the model actually does
[13:43] and let's say the model actually does that if i take
[13:45] that if i take w transpose x and i push that through
[13:47] w transpose x and i push that through
[13:48] w transpose x and i push that through the sigmoid then i get a
[13:49] the sigmoid then i get a value very close to 1 which is what i
[13:51] value very close to 1 which is what i want the label for this thing is a 1
[13:53] want the label for this thing is a 1 as stated here in that case what will
[13:57] as stated here in that case what will happen to w how will we
[13:58] happen to w how will we update the model parameters or 1 minus 1
[14:02] update the model parameters or 1 minus 1 is equal to 0 or very close to 0 if if
[14:05] is equal to 0 or very close to 0 if if the prediction is very close to 1.
[14:07] the prediction is very close to 1. in other words we will only update w
[14:10] in other words we will only update w in a very very small way or in no way at
[14:13] in a very very small way or in no way at all the opposite is also
[14:15] all the opposite is also true if the prediction is really bad in
[14:18] true if the prediction is really bad in other words we know this thing is
[14:19] other words we know this thing is
[14:20] other words we know this thing is labeled with a one but let's say the
[14:21] labeled with a one but let's say the model
[14:22] model outputs the output of the sigmoid here
[14:24] outputs the output of the sigmoid here is very close to zero
[14:25] is very close to zero in that case we're going to have a much
[14:27] in that case we're going to have a much larger update
[14:29] larger update here and that's one way of seeing that
[14:32] here and that's one way of seeing that actually
[14:33] actually the biggest effect on the updates
[14:36] the biggest effect on the updates and by implication on the loss will be
[14:39] and by implication on the loss will be from the training points which are
[14:43] from the training points which are basically badly classified by the model
[14:45] basically badly classified by the model at the moment
[14:46] at the moment so let's look at it a little bit more
[14:48] so let's look at it a little bit more practically
[14:49] practically on actual data so here we've got the
[14:51] on actual data so here we've got the iris data set and we've converted it
[14:54] iris data set and we've converted it into a two-dimensional problem we've got
[14:56] into a two-dimensional problem we've got petal length
[14:57] petal length petal width and we just want to do a
[14:59] petal width and we just want to do a prediction of whether a flower is a iris
[15:02] prediction of whether a flower is a iris virginica
[15:03] virginica or not something else if we
[15:06] or not something else if we fit a binary logistic regression model
[15:08] fit a binary logistic regression model to this data
[15:09] to this data then the decision boundary is the one
[15:11] then the decision boundary is the one ending up here
[15:12] ending up here and by implication this means that our
[15:14] and by implication this means that our weight vector would be
[15:16] weight vector would be pointing in this direction towards the
[15:19] pointing in this direction towards the positive clauses
[15:20] positive clauses it will be orthogonal to our decision
[15:23] it will be orthogonal to our decision boundary there
[15:24] boundary there one other thing we can do is we can
[15:26] one other thing we can do is we can actually visualize
[15:27] actually visualize the probabilities for different points
[15:30] the probabilities for different points in this
[15:31] in this feature space so here what i've done is
[15:33] feature space so here what i've done is i've just colored
[15:34] i've just colored the space and the more red a point is
[15:38] the space and the more red a point is the more positive the model is
[15:40] the more positive the model is predicting that that point is for being
[15:42] predicting that that point is for being an iris virginica
[15:43] an iris virginica and the more bluer point is the more the
[15:46] and the more bluer point is the more the model is predicting that this thing is
[15:48] model is predicting that this thing is not an iris virginica
[15:49] not an iris virginica so values close to one output values
[15:52] so values close to one output values close to one would be this dark red
[15:53] close to one would be this dark red color
[15:54] color output values from our model close to
[15:56] output values from our model close to zero would be this blue color
[15:58] zero would be this blue color what you can see here is that clearly a
[16:01] what you can see here is that clearly a point lying somewhere here
[16:02] point lying somewhere here that is definitely iris virginica a
[16:05] that is definitely iris virginica a point lying somewhere here is definitely
[16:07] point lying somewhere here is definitely not an iris virginica
[16:09] not an iris virginica and then close to the decision boundary
[16:11] and then close to the decision boundary from the previous slide which runs
[16:12] from the previous slide which runs somewhere here
[16:14] somewhere here there's a little bit more ambiguity so
[16:16] there's a little bit more ambiguity so just off the decision boundary you will
[16:18] just off the decision boundary you will have a probability
[16:19] have a probability higher than 0.5 and just off it on the
[16:22] higher than 0.5 and just off it on the other side you will have a probability
[16:24] other side you will have a probability just lower than 0.5
[16:26] just lower than 0.5 so here the model actually makes a
[16:28] so here the model actually makes a mistake this will be classified as an
[16:31] mistake this will be classified as an iris virginica
[16:32] iris virginica although it is actually not an iris
[16:33] although it is actually not an iris
[16:34] although it is actually not an iris virginica but the probability that the
[16:36] virginica but the probability that the model assigns to this one is relatively
[16:38] model assigns to this one is relatively close to 0.5
[16:40] close to 0.5 so that's pretty cool the model almost
[16:42] so that's pretty cool the model almost gives us a score telling us how
[16:43] gives us a score telling us how
[16:44] gives us a score telling us how confident it is
[16:45] confident it is in its prediction so here we've got
[16:48] in its prediction so here we've got another visualization where we've got an
[16:50] another visualization where we've got an x1 that's the petal length and x2 the
[16:53] x1 that's the petal length and x2 the petal width
[16:54] petal width and it's the same data as we saw on the
[16:56] and it's the same data as we saw on the previous slide but what i've done now is
[16:58] previous slide but what i've done now is on the set axis i've plotted the
[17:01] on the set axis i've plotted the probability of being in the positive
[17:03] probability of being in the positive clause given some
[17:04] clause given some input vector feature vector x
[17:07] input vector feature vector x and our parameter vector w the one that
[17:11] and our parameter vector w the one that we fit and you can see here now we can
[17:13] and you can see here now we can visualize it a lot more clearly
[17:15] visualize it a lot more clearly that if we're somewhere here around here
[17:18] that if we're somewhere here around here in the x
[17:19] in the x space then we're going to definitely be
[17:21] space then we're going to definitely be classified as an iris virginica
[17:23] classified as an iris virginica if we're somewhere here then the
[17:25] if we're somewhere here then the probability of being an iris virginica
[17:27] probability of being an iris virginica is very close to zero
[17:29] is very close to zero so one question that might come up is we
[17:31] so one question that might come up is we now know that
[17:32] now know that w is some vector orthogonal to the
[17:35] w is some vector orthogonal to the decision boundary
[17:36] decision boundary fine but what happens if i keep the
[17:39] fine but what happens if i keep the direction of w
[17:41] direction of w fixed but i just make this vector longer
[17:43] fixed but i just make this vector longer
[17:44] fixed but i just make this vector longer and longer in other words i
[17:45] and longer in other words i increase the length of w what effect
[17:48] increase the length of w what effect does that have
[17:49] does that have on the model so what i've done in the
[17:51] on the model so what i've done in the next few slides is i've actually kept
[17:53] next few slides is i've actually kept this w but i just made it
[17:56] this w but i just made it very very very long let's see what
[17:57] very very very long let's see what happens so you have got the same
[18:00] happens so you have got the same figure as before where a dark red
[18:02] figure as before where a dark red indicates
[18:03] indicates a value close to one for the output of
[18:06] a value close to one for the output of the model and a dark blue indicates a
[18:07] the model and a dark blue indicates a
[18:08] the model and a dark blue indicates a value close to zero and what you can see is
[18:11] close to zero and what you can see is that with a very very large
[18:12] that with a very very large w the confidence around your decision
[18:16] w the confidence around your decision boundary has changed quite a lot
[18:18] boundary has changed quite a lot for points here and here the model
[18:21] for points here and here the model outputs a value close to one and close
[18:23] outputs a value close to one and close to zero and that hasn't changed much
[18:25] to zero and that hasn't changed much but for the points close to the decision
[18:27] but for the points close to the decision boundary you can see that we're making
[18:29] boundary you can see that we're making much more sharper predictions for the
[18:32] much more sharper predictions for the model
[18:33] model that's even more clear when we actually
[18:35] that's even more clear when we actually visualize the probability surface
[18:37] visualize the probability surface so here you can see that we've got this
[18:40] so here you can see that we've got this very very sharp edge here
[18:42] very very sharp edge here where on just this side of the edge
[18:44] where on just this side of the edge we're very confident that it isn't an
[18:46] we're very confident that it isn't an iris virginica and just on the other
[18:48] iris virginica and just on the other side of the edge
[18:49] side of the edge we're very confident confident that it
[18:51] we're very confident confident that it
[18:52] we're very confident confident that it is indeed iris virginica so let's just summarize
[18:56] iris virginica so let's just summarize everything we saw
[18:57] everything we saw in this video the one thing is that the
[18:59] in this video the one thing is that the bias term
[19:00] bias term w0 basically just offsets the decision
[19:04] w0 basically just offsets the decision boundary
[19:05] boundary the direction of w or weight vector or
[19:08] the direction of w or weight vector or parameter vector influences the
[19:10] parameter vector influences the direction of the decision boundary
[19:12] direction of the decision boundary more specifically w is always orthogonal
[19:15] more specifically w is always orthogonal to the decision boundary
[19:17] to the decision boundary and when i use w here just for the
[19:20] and when i use w here just for the moment i'm not including w
[19:21] moment i'm not including w 0 into that vector here the length of w
[19:25] 0 into that vector here the length of w again ignoring w0 influences the
[19:28] again ignoring w0 influences the steepness of the decision boundary so if
[19:30] steepness of the decision boundary so if we have a very very
[19:32] we have a very very large w something with a very big norm
[19:34] large w something with a very big norm then we will have a much more steeper
[19:36] then we will have a much more steeper decision boundary and if we are in that
[19:39] decision boundary and if we are in that setting with a very large w
[19:40] setting with a very large w then points that are very close but just
[19:43] then points that are very close but just off the decision boundary
[19:45] off the decision boundary will still be assigned a very high or
[19:47] will still be assigned a very high or very low probability
[19:49] very low probability
[19:50] very low probability if we have a small w in contrast
[19:52] if we have a small w in contrast something that's
[19:53] something that's shorter than the w here then the
[19:55] shorter than the w here then the probability assignment over the decision
[19:57] probability assignment over the decision boundary will be more gradual
[20:00] boundary will be more gradual it's quite interesting how much we can
[20:02] it's quite interesting how much we can just see from
[20:03] just see from a single weight vector in binary
[20:05] a single weight vector in binary logistic regression
[20:07] logistic regression one thing that is a bit interesting in
[20:09] one thing that is a bit interesting in logistic regression
[20:11] logistic regression is that although in some way it is a
[20:12] is that although in some way it is a non-linear model it has that sigmoid
[20:15] non-linear model it has that sigmoid function
[20:16] function the decision boundary is still a linear
[20:18] the decision boundary is still a linear function it's a straight line
[20:20] function it's a straight line in this feature parameter space and
[20:23] in this feature parameter space and in the next video we will see how we can
[20:26] in the next video we will see how we can actually
[20:27] actually allow logistic regression to make
[20:29] allow logistic regression to make non-linear
[20:30] non-linear decisions
