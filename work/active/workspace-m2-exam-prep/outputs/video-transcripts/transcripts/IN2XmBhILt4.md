---
video_id: IN2XmBhILt4
url: https://www.youtube.com/watch?v=IN2XmBhILt4
title: Neural Networks Pt. 2: Backpropagation Main Ideas
channel: StatQuest with Josh Starmer
duration: 17:33
language: en
unit: L15
status: OK
---

[00:00] Backpropagation is a really big word, but it's not a really big deal. StatQuest!
[00:08] Hello!
[00:09] I'm Josh Starmer and welcome to StatQuest!
[00:11] Today we're going to talk about Neural Networks, Part 2: Backpropagation Main Ideas.
[00:19] Note: this StatQuest assumes that you are already familiar with neural networks, the
[00:25] chain rule, and gradient descent. If not, check out the quests. The links are in the description below.
[00:35] In the StatQuest on Neural Networks Part 1, Inside the Black Box, we started with
[00:42] a simple dataset that showed whether or not different drug dosages were effective against a virus.
[00:49] The low and high dosages were not effective, but the medium dosage was effective.
[00:57] Then&nbsp;we talked about how a neural network like this one fits a green squiggle to this data set.
[01:05] Remember, the neural network starts with identical activation functions, but, using
[01:12] different weights and biases on the connections, it flips and stretches the activation
[01:18] functions into new shapes, which are then added together to get a squiggle that is shifted to fit the data.
[01:27] However, we did not talk about how to estimate the weights and biases.
[01:33] So let's talk about how backpropagation optimizes the weights and biases in this, and other, neural networks.
[01:42] Note: backpropagation is relatively simple, but there are a ton of details, so I split it up into bite-sized pieces.
[01:52] In this part we talk about the main ideas of backpropagation.
[01:58] One: using the chain rule to calculate derivatives, and Two: plugging the derivatives
[02:04] into gradient descent to optimize parameters. In the next part we'll talk about how
[02:11] the chain rule and gradient descent apply to multiple parameters simultaneously, and introduce some fancy notation.
[02:21] Then we will go completely bonkers with the chain rule and show how to optimize all
[02:26] seven parameters simultaneously in this neural network.
[02:31] Bam!
[02:34] First, so we can be clear about which specific weights we are talking about, let's
[02:41] give each one a name: we have w1, w2, w3, and w4.
[02:51] And let's name each bias: b1, b2, and b3.
[03:00] Note: conceptually, backpropagation starts with the last parameter and works its way
[03:06] backwards to estimate all of the other parameters.
[03:11] However, we can discuss all of the main ideas behind a backpropagation by just estimating the last bias, b3.
[03:21] So, in order to start from the back, let's assume that we already have optimal values
[03:28] for all of the parameters&nbsp;except for the last bias term, b3.
[03:34] Note: throughout this, and the next StatQuests, I'll make the parameter values that
[03:40] have already been optimized green, and unoptimized parameters will be red.
[03:47] Also, note: to keep the math simple, let's assume dosages go from 0, for low, to 1, for high.
[03:56] Now, if we run dosages from 0 to 1 through the connection to the top node in the hidden
[04:04] layer, then we get the x-axis coordinates for the activation function, that are all
[04:11] inside this red box&nbsp;and when we plug the x-axis coordinates into the activation function
[04:18] which, in this example, is the soft plus activation function, we get the corresponding
[04:26] y-axis coordinates, and this blue curve.
[04:30] Then we multiply the y-axis coordinates on the blue curve by negative 1.22 and we get the final blue curve.
[04:40] Bam!
[04:42] Now, if we run dosages from zero to one through the connection to the bottom node
[04:48] in the hidden layer, then we get x-axis coordinates inside this red box.
[04:56] Now we plug those x-axis coordinates into the activation function to get the corresponding
[05:04] y-axis coordinates for this orange curve.
[05:08] Now we multiply the y-axis coordinates on the orange curve by negative 2.3 and we end up with this final orange curve.
[05:19] Bam!
[05:22] Now we add the blue and orange curves together to get this green squiggle.
[05:29] Now we are ready to add the final bias, b3, to the green squiggle.
[05:35] Because we don't yet know the optimal value for b3, we have to give it an initial
[05:41] value,&nbsp;and because bias terms are frequently initialized to 0, we will set b3 equal to 0.
[05:50] Now, adding zero to all of the y-axis coordinates on the green squiggle leaves it right where it is.
[05:58] However, that means the green squiggle is pretty far from the data that we observed.
[06:05] We can quantify how good the green squiggle fits the data by calculating the sum of the squared residuals.
[06:12] A residual is the difference between the observed and predicted values.
[06:18] For example, this residual is the observed value, zero, minus the predicted value
[06:25] from the green squiggle, negative 2.6. This residual is the observed value, one,
[06:33] minus the predicted value from the green squiggle, negative 1.61.
[06:41] Lastly, this residual is the observed value, 0, minus the predicted value from the green squiggle, negative 2.61.
[06:52] Now we square each residual and add them all together to get 20.4 for the sum of the squared residuals.
[07:03] So when b3 equals 0, the sum of the squared residuals equals 20.4. And that corresponds
[07:13] to this location on this graph that has the sum of the squared residuals on the y -axis and the bias, b3, on the x-axis.
[07:24] Now, if we increase b3 to 1, then we would add one to the y-axis coordinates on the
[07:33] green squiggle and shift the green squiggle up one.
[07:38] And we end up with shorter residuals.
[07:42] When we do the math, the sum of the squared residuals equals 7.8,&nbsp;and that corresponds to this point on our graph.
[07:55] If we increase b3 to 2, then the sum of the squared residuals equals 1.11. And if
[08:03] we increase b3 to 3, then the sum of the squared residuals equals 0.46. And if we
[08:12] had time to plug in tons of values for b3, we would get this pink curve, and we could
[08:18] find the lowest point, which corresponds to the value for b3 that results in the
[08:24] lowest sum of the squared residuals, here.
[08:28] However, instead of plugging in tons of values to find the lowest point in the pink
[08:34] curve, we use gradient descent to find it relatively quickly.
[08:39] And that means we need to find the derivative of the sum of the squared residuals with respect to b3.
[08:47] Now, remember the sum of the squared residuals equals the first residual squared,
[08:54] plus all of the other squared residuals.
[08:58] Now, because this equation takes up a lot of space, we can make it smaller by using summation notation.
[09:08] The greek symbol sigma tells us to sum things together, and 'i' is an index for the
[09:15] observed and predicted values that starts at one.
[09:20] And the index goes from one to the number of values, 'n', which in this case is set to 3.
[09:28] So, when 'i' equals one, we're talking about the first residual.
[09:34] When 'i' equals two, we're talking about the second residual.
[09:39] And when 'i' equals three, we are talking about the third residual.
[09:44] Now let's talk a little bit more about the predicted values.
[09:49] Each predicted value comes from the green squiggle, and the green squiggle comes from the last part of the neural network.
[09:59] In other words, the green squiggle is the sum of the blue and orange curves, plus b3.
[10:08] Now remember, we want to use gradient descent to optimize b3, and that means we need
[10:15] to take the derivative of the sum of the squared residuals with respect to b3.
[10:22] And because the sum of the squared residuals are linked to b3 by the predicted values,
[10:30] we can use the chain rule to solve for the derivative of the sum of the squared residuals with respect to b3.
[10:41] The chain rule says that the derivative of the sum of the squared residuals with respect
[10:46] to b3 is the derivative of the sum of the squared residuals with respect to the predicted
[10:52] values, times the derivative of the predicted values with respect to b3.
[10:59] Now, before we calculate the derivative of the sum of the squared residuals with respect
[11:05] to the predicted values, let's clean up our workspace and move these equations out of the way.
[11:13] Now we can solve for the derivative of the sum of the squared residuals with respect
[11:19] to the predicted values by first substituting in the equation, and then use the chain
[11:25] rule to move the square to the front, and then we multiply that by the derivative
[11:30] of the stuff inside the parentheses with respect to the predicted values,&nbsp;negative one.
[11:37] Now we simplify by multiplying two by negative 1, and we have the derivative of the
[11:43] sum of the squared residuals with respect to the predicted values.
[11:49] So let's move that up here,&nbsp;and now we are done with the first part.
[11:55] Now let's solve for the second part: the derivative of the predicted values with respect to b3.
[12:03] We start by plugging in the equation for the predicted values.
[12:08] Remember, the blue and orange curves were created before we got to b3.
[12:14] So the derivative of the blue curve with respect to b3 is 0, because the blue curve is independent of b3.
[12:24] And the derivative of the orange curve with respect to b3 is also 0.
[12:30] Lastly, the derivative of b3, with respect to b3, is 1.
[12:36] Now we just add everything up, and the derivative of the predicted values with respect to b3, is one.
[12:46] So we multiply the derivative of the sum of the squared residuals with respect to the predicted values by 1.
[12:54] Note: this times 1 part in the equation doesn't do anything, but I'm leaving it in
[13:00] to remind us that the derivative of the sum of the squared residuals with respect
[13:05] to b3 consists of two parts: the derivative of the sum of the squared residuals with
[13:12] respect to the predicted values, and the derivative of the predicted values with respect to b3.
[13:20] Bam! And at long last we have the derivative of the sum of the squared residuals with respect to b3.
[13:30] And that means we can plug this derivative into gradient descent to find the optimal value for b3.
[13:38] So let's move this equation up and show how we can use this equation with gradient descent.
[13:45] Note: if you're not familiar with gradient descent, check out the quest
[13:50] the link is in the description below.
[13:53] Anyway, first, we expand the summation.
[13:58] Then, we plug in the observed values and the values predicted by the green squiggle.
[14:05] Remember, we get the predicted values on the green squiggle by running the dosages through the neural network.
[14:13] Now, we just do the math and get negative 15.7. And that corresponds to the slope for when b3 equals zero.
[14:25] Now we plug the slope into the gradient descent equation for step size, and, in this
[14:31] example, we'll set the learning rate to 0.1. And that means the step size is -1.57.
[14:41] Now we use the step size to calculate the new value for b3 by plugging in the current
[14:47] value for b3, zero, and the step size, -1.57. And the new value for b3 is 1.57.
[15:00] Changing b3 to 1.57 shifts the green squiggle up, and that shrinks the residuals.
[15:09] Now, plugging in the new predicted values and doing the math gives us -6.26, which
[15:17] corresponds to the slope when b3 equals 1.57.
[15:23] Then, we calculate the step size and the new value for b3, which is 2.19.
[15:34] Changing b3 to 2.19 shifts the green squiggle up further, and that shrinks the residuals even more.
[15:44] Now we just keep taking steps until the step size is close to zero. And because the
[15:51] step size is close to 0 when b3 equals 2.61, we decide that 2.61 is the optimal value for b3.
[16:03] Double bam!
[16:06] So, the main ideas for backpropagation are that, when a parameter is unknown, like
[16:13] b3, we use the chain rule to calculate the derivative of the sum of the squared residuals
[16:19] with respect to the unknown parameter, which in this case was b3.
[16:25] Then we initialize&nbsp;the unknown parameter with a number, and in this case we set b3
[16:31] equal to zero, and used gradient descent to optimize the unknown parameter.
[16:39] Triple bam!
[16:42] In the next StatQuest we'll show how these ideas can be used to optimize all of the parameters in a neural network.
[16:50] Now it's time for some shameless self-promotion.
[16:56] If you want to review statistics and machine learning offline, check out the StatQuest study guides at statquest.org.
[17:04] There's something for everyone.
[17:06] Hooray!
[17:07] We've made it to the end of another exciting StatQuest.
[17:11] If you like this StatQuest and want to see more, please subscribe. And if you want
[17:16] to support StatQuest, consider contributing to my patreon campaign, becoming a channel
[17:22] member, buying one or two of my original songs, or a t-shirt or a hoodie, or just
[17:27] donate the links are in the description below. Alright, until next time. Quest on!
