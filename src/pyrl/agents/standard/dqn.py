from pyrl import Agent
from pyrl.replay_buffer.replay_buffer import ReplayMemory
from collections import namedtuple
import math
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from collections.abc import Iterable
import numpy as np


Transition = namedtuple('Transition',
                        ('state', 'action', 'next_state', 'reward', 'done'))


class DQN(nn.Module):

    def __init__(self, n_observations, n_actions, batch_size):
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(n_observations, batch_size).float()
        self.layer2 = nn.Linear(batch_size, batch_size).float()
        self.layer3 = nn.Linear(batch_size, batch_size).float()
        self.layer4 = nn.Linear(batch_size, batch_size).float()
        self.layer5 = nn.Linear(batch_size, batch_size).float()
        
        self.layer6 = nn.Linear(batch_size, batch_size).float()
        self.layer7 = nn.Linear(batch_size, batch_size).float()
        self.layer8 = nn.Linear(batch_size, batch_size).float()
        self.layer9 = nn.Linear(batch_size, batch_size).float()
        self.layer10 = nn.Linear(batch_size, n_actions).float()

    def forward(self, x):
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        x = F.relu(self.layer3(x))
        x = F.relu(self.layer4(x))
        
        x = F.relu(self.layer5(x))
        x = F.relu(self.layer6(x))
        x = F.relu(self.layer7(x))
        x = F.relu(self.layer8(x))
        x = F.relu(self.layer9(x))
        
        return self.layer10(x)

class DQNAgent(Agent):
    """
        Deep Q-Network Agent.
    """
    
    def __init__(self, observation_space, action_space, initial_budget=1000,
                 exploration_rate=None, eps_start=0.9, eps_end=0.05, eps_decay=100,
                 replay_capacity=1000, batch_size=128, gamma=0.95,
                 learning_rate=1e-3, tau=0.005, store_N=True
                 ):
        super().__init__(observation_space=observation_space, action_space=action_space, initial_budget=initial_budget)
        
        self.eps_start = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        
        self.policy_net = DQN(2, self.action_space.n, batch_size=self.batch_size).to(self.device)
        self.target_net = DQN(2, self.action_space.n, batch_size=self.batch_size).to(self.device)
        
        self.replay_buffer = ReplayMemory(replay_capacity)
        self.gamma = gamma
        self.lr = learning_rate
        self.tau = tau
        self.optimizer = optim.AdamW(self.policy_net.parameters(), lr=self.lr, amsgrad=True)        
        self.b = self.initial_budget
        self.store_N = store_N
        self.exploration_rate = exploration_rate
        
    def reset(self, s, reset_knowledge=True, reset_budget=True, learning=True):
        self.t = 0 # time, or number of elapsed rounds
        self.s = s  if isinstance(s, Iterable)  else  [s] # memory of the current state and last received reward
        self.r = 0.0
        
        if reset_knowledge:
            self.Q = np.random.sample(self.observation_shape + self.action_shape)
                
            if self.store_N:
               self.N = np.zeros(self.observation_shape + self.action_shape, dtype=int)

            self.policy_net = DQN(2, self.action_space.n, batch_size=self.batch_size).to(self.device)
            self.target_net = DQN(2, self.action_space.n, batch_size=self.batch_size).to(self.device)
            self.replay_buffer.clear()      
            self.optimizer = optim.AdamW(self.policy_net.parameters(), lr=self.lr, amsgrad=True)
            
        self.b = self.initial_budget
        self.a = self.action_space.sample() # next chosen action
        
        
    def choose_action(self):
        sample = random.random()
        
        if self.exploration_rate:        
            eps_threshold = self.exploration_rate
        else:
            eps_threshold = self.eps_end + (self.eps_start - self.eps_end) * math.exp(-1. * self.t / self.eps_decay)
                 
        if sample > eps_threshold:
            with torch.no_grad():
                self.policy_net.eval()
                self.a = self.policy_net(torch.tensor(self.s, dtype=torch.float).unsqueeze(0)).argmax().view(1,1)
                return self.a.item()
        else:
            self.a = torch.tensor([[self.action_space.sample()]], device=self.device)
            return self.a.item()

    def observe(self, s, r, terminated=False, truncated=False):
        """
            Memorize the observed state and received reward.
        """
        self.prev_s = self.s
        self.s = s  if isinstance(s, Iterable)  else  [s]
        self.r = r
        self.t += 1
        self.b += r
        self.replay_buffer.push(self.prev_s, self.a, self.s, self.r, terminated) # Store the transition in memory
        index_sa = self.get_state_tpl(self.prev_s) + self.get_action_tpl()

        if self.store_N:
           self.N[index_sa] += 1
           
    
    def learn(self):
        if len(self.replay_buffer) < self.batch_size:
            return
        
        minibatch = random.sample(self.replay_buffer, self.batch_size) #J
        state1_batch = torch.stack([torch.tensor(s1, dtype=torch.float) for (s1,a,r,s2,d) in minibatch]) #K
        action_batch = torch.Tensor([a for (s1,a,r,s2,d) in minibatch])
        reward_batch = torch.Tensor([r for (s1,a,r,s2,d) in minibatch])
        state2_batch = torch.stack([torch.tensor(s2, dtype=torch.float) for (s1,a,r,s2,d) in minibatch])
        done_batch = torch.Tensor([d for (s1,a,r,s2,d) in minibatch])
        
        Q1 = self.policy_net(state1_batch) #L
        with torch.no_grad():
            Q2 = self.policy_net(state2_batch) #M
        
        Y = reward_batch + self.gamma * ((1 - done_batch) * torch.max(Q2,dim=1)[0]) #N
        X = Q1.gather(dim=1, index=action_batch.long().unsqueeze(dim=1)).squeeze()
        loss_fn = torch.nn.MSELoss()
        loss = loss_fn(X, Y.detach())
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        for x in range(self.observation_shape[0]):
            for y in range(self.observation_shape[1]):
                self.Q[x][y] = self.policy_net(torch.tensor([x, y], dtype=torch.float).unsqueeze(0)).detach().numpy()
        

        # transitions, indices, weights = self.replay_buffer.sample(self.batch_size)
        # batch = Transition(*zip(*transitions))
        # non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
        #                                     batch.next_state)), device=self.device, dtype=torch.bool)
        # non_final_next_states = torch.stack([torch.tensor(s, dtype=torch.float) for s in batch.next_state if s is not None])

        # state_batch = torch.stack([torch.tensor(s, dtype=torch.float).to(self.device) for s in batch.state])
        # reward_batch = torch.stack([torch.tensor(s, dtype=torch.float).to(self.device) for s in batch.reward])

        # state_action_values = self.policy_net(state_batch)
            
        # next_state_values = torch.zeros((self.batch_size), dtype=torch.float, device=self.device)
        # with torch.no_grad():
        #     next_state_values[non_final_mask] = self.target_net(non_final_next_states).max(1)[0]

        # # Compute the expected Q values
        # expected_state_action_values = (next_state_values * self.gamma) + reward_batch

        # # Compute Huber loss
        # criterion = nn.SmoothL1Loss()
        # loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

        # # Optimize the model
        # self.optimizer.zero_grad()
        # loss.backward()
        
        # # In-place gradient clipping
        # torch.nn.utils.clip_grad_value_(self.policy_net.parameters(), 100)
        # self.optimizer.step()
        
        # target_net_state_dict = self.target_net.state_dict()
        # policy_net_state_dict = self.policy_net.state_dict()
        # for key in policy_net_state_dict:
        #     target_net_state_dict[key] = policy_net_state_dict[key]*self.tau + target_net_state_dict[key]*(1-self.tau)
        # self.target_net.load_state_dict(target_net_state_dict)
        
        # for x in range(self.observation_shape[0]):
        #     for y in range(self.observation_shape[1]):
        #         for z in range(self.action_shape[0]):
        #             self.Q[x][y][z] = self.policy_net(torch.tensor([x, y], dtype=torch.float).unsqueeze(0)).max()
        #             self.Q[x][y][z] = 0
                    