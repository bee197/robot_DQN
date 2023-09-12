import parl
import paddle
import numpy as np
from paddle.distribution import Categorical
import paddle.nn.functional as F


class PPOAgent(parl.Agent):
    def __init__(self, algorithm, model):
        super(PPOAgent, self).__init__(algorithm)
        self.alg = algorithm
        self.model = model

    def sample(self, obs, rpm):
        obs = paddle.to_tensor(obs)
        value, action, action_log_probs, action_entropy = self.alg.sample(obs)

        value_numpy = value.detach().numpy()
        action_numpy = action.detach().numpy()[0]
        action_log_probs_numpy = action_log_probs.detach().numpy()[0]
        action_entropy_numpy = action_entropy.detach().numpy()

        return value_numpy, action_numpy, action_log_probs_numpy, action_entropy_numpy

    def predict(self, obs):
        obs = paddle.to_tensor(obs)
        action = self.alg.predict(obs)

        return action

    def value(self, obs):
        obs = paddle.to_tensor(obs, dtype='float32')
        # obs升维
        obs = paddle.unsqueeze(obs, axis=0)
        value = self.alg.value(obs)
        value = value.detach().numpy()
        return value

    def learn(self, rpm):
        value_loss_epoch = 0
        action_loss_epoch = 0
        entropy_loss_epoch = 0
        # 创建一个从0到batch_size-1的连续数组索引。
        indexes = np.arange(1000)
        for _ in range(4):
            # 打乱batch顺序
            np.random.shuffle(indexes)
            for start in range(0, 1000, 250):
                end = start + 250
                sample_idx = indexes[start:end]
                batch_obs, batch_action, batch_logprob, batch_adv, batch_return, batch_value = rpm.sample_batch(
                    sample_idx)
                batch_obs = paddle.to_tensor(batch_obs)
                batch_action = paddle.to_tensor(batch_action)
                batch_logprob = paddle.to_tensor(batch_logprob)
                batch_adv = paddle.to_tensor(batch_adv)
                batch_return = paddle.to_tensor(batch_return)
                batch_value = paddle.to_tensor(batch_value)

                value_loss, action_loss, entropy_loss = self.alg.learn(
                    batch_obs, batch_action, batch_value, batch_return,
                    batch_logprob, batch_adv)

                value_loss_epoch += value_loss
                action_loss_epoch += action_loss
                entropy_loss_epoch += entropy_loss

        value_loss_epoch /= 1000
        action_loss_epoch /= 1000
        entropy_loss_epoch /= 1000

        return value_loss_epoch, action_loss_epoch, entropy_loss_epoch

