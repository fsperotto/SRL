from tensorforce.environments import Environment
import numpy as np
import gymnasium as gym
from pyrl import pyrl_space
import pygame as pg
from typing import Tuple, List, Union, Callable, Iterable


from pyrl import PyGameGUI

class TFGridEnv(Environment):
    """
        Survival Grid Environment adapted for Tensorforce Methods
    """
    
    metadata = {"render_modes": ["human", "rgb_array", "external"], "render_fps": 90}
    
    def __init__(self, render_mode: str=None, 
                 size: Union[None, int, Tuple[int, int]]=None,
                 num_rows=None, num_cols=None,
                 terminate=False,
                 reward_matrix=None,
                 reward_targets=None,
                 default_reward:float=0.0,
                 reward_mode="s'",  # "sas'" , "as'" , "sa", "a" , "s'",
                 random=False) -> None:
        
        super().__init__()
        
        self.render_mode = render_mode
        self.interrupted = False
        
        #define grid size from parameters
        if (num_rows is not None or num_cols is not None):
            if size is not None:
                print('Warning: GridEnv - ignoring size parameter, since num_rows or num_cols are given.')
            if num_rows is not None:
                self.num_rows = num_rows
                if num_cols is not None:
                    self.num_cols = num_cols
                else:
                    self.num_cols = num_rows
            else:
                self.num_cols = num_cols
                self.num_rows = num_cols
            self.size = np.array( (self.num_cols, self.num_rows) )
        else:
            if size is not None:
                if not isinstance(size, tuple) and not isinstance(size, list):
                    self.size = np.array([size, size])
                else:
                    self.size = np.array(size)
            else:
                self.size=np.array([20,20])
            self.num_cols = self.size[0]
            self.num_rows = self.size[1]
        
        state_space = gym.spaces.MultiDiscrete((self.num_rows, self.num_cols))
        self.observation_space = state_space
        
        self.num_actions = 4
        action_space = gym.spaces.Discrete(self.num_actions)
        self.action_space = action_space
        
        self._action_to_direction = {
            0: np.array([1, 0]),  #right
            1: np.array([0, 1]),  #down
            2: np.array([-1, 0]), #left
            3: np.array([0, -1]), #up
        }

        self.reward_mode = reward_mode
        
        self.default_reward = default_reward

        if reward_matrix is not None:
            self.reward_matrix = np.array(reward_matrix)
            self.reward_targets = None
            if reward_targets is not None:
                print("WARNING: GridEnv cannot receive reward matrix and reward targets")
        else:
            if reward_targets is not None:
                self.reward_matrix = np.full((self.num_cols, self.num_rows), self.default_reward)
                self.reward_targets = reward_targets
                for r, pos_list in reward_targets.items():
                    for x, y in pos_list:
                        self.reward_matrix[x, y] = r
            else:
                self.reward_matrix = 2 * np.random.sample((self.num_cols, self.num_rows)) - 1
                self.reward_targets = None

        self._render_frame = None

        self._agent_location = np.array([0, 0])
        
        self.terminate = terminate
        self.window = None
        self.clock = None
        
        #observations (what the agent perceives from the environment state)
        self.observation_space, self.observation_shape, self.num_obs_var, self.num_obs_comb = pyrl_space(self.observation_space)        
        #actions
        self.action_space, self.action_shape, self.num_act_var, self.num_act_comb = pyrl_space(self.action_space)


    def states(self):
        return dict(type='int', shape=(2,), num_values=(self.num_rows * self.num_cols))

    def actions(self):
        return dict(type='int', num_values=self.action_space.n)


    def _get_obs(self) -> int:
        return self._agent_location

    def _get_info(self) -> dict:
        return dict()
    
    def get_reward_matrix(self):
       R = self.reward_matrix
       return R
       
    def get_transition_matrix(self):
       #P = np.array( [[[(x, y) for x in reange(self.num_cols)] for y in range(self.num_rows)] for a in range(4) )
       return None
    
    
    # Optional: should only be defined if environment has a natural fixed
    # maximum episode length; otherwise specify maximum number of training
    # timesteps via Environment.create(..., max_episode_timesteps=???)
    def max_episode_timesteps(self):
        return super().max_episode_timesteps()

    def reset(self):
        self.t = 0
        
        if self.num_rows == self.num_cols:
            self._agent_location = np.array([0, 0])
        else:
            self._agent_location = np.array([0, self.num_rows // 2])

        observation = self._get_obs()
        info = self._get_info()
        self.truncated = False        
        
        if self.render_mode is not None:
            if self._render_frame is not None:
               self._render_frame()

        return observation, info
    
    def step(self, actions):
        
        done = False
        self.t = self.t + 1
        
        direction = self._action_to_direction[actions]
        self._agent_location = np.clip(
            self._agent_location + direction, [0, 0], [self.num_cols - 1 , self.num_rows - 1]
        )
        observation = self._get_obs()
        info = self._get_info()

        #if self.render_mode is not None:
        #    self._render_frame()

        reward = self.reward_matrix.item(tuple(self._agent_location))

        if self.terminate and reward == self.reward_targets.items()[0][0]:
            done = True
        
        return observation, reward, done, self.truncated, info
        # return observation, done, reward
    
    def close(self) -> None:
        pass
    
    # def render(self):
    #     if self.render_mode is not None:
    #         if self._render_frame is not None:
    #            return self._render_frame()

    # def _render_frame(self):
    #     if self.window is None and self.render_mode == "human":
    #         pg.init()
    #         pg.display.init()
    #         self.window = pg.display.set_mode(
    #             (self.window_size, self.window_size)
    #         )
    #     if self.clock is None and self.render_mode == "human":
    #         self.clock = pg.time.Clock()

    #     canvas = pg.Surface((self.window_size, self.window_size))
    #     canvas.fill((255, 255, 255))
    #     pix_square_size = (
    #         self.window_size / self.size[0]
    #     )

    #     for label, target_location in self._target_locations.items():
    #         pg.draw.rect(
    #             canvas,
    #             (255, 0 if label == "major" else 165, 0),
    #             pg.Rect(
    #                 pix_square_size * target_location,
    #                 (pix_square_size, pix_square_size),
    #             ),
    #         )

    #     pg.draw.circle(
    #         canvas,
    #         (255, 0, 0) if self.recharge_mode else (0, 0, 255),
    #         (self._agent_location + 0.5) * pix_square_size,
    #         pix_square_size / 3,
    #     )

    #     for x in range(self.size[1] + 1):
    #         pg.draw.line(
    #             canvas,
    #             0,
    #             (0, pix_square_size * x),
    #             (self.size[0] * pix_square_size, pix_square_size * x),
    #             width=3,
    #         )

    #     for x in range(self.size[0] + 1):
    #         pg.draw.line(
    #             canvas,
    #             0,
    #             (pix_square_size * x, 0),
    #             (pix_square_size * x, self.size[1] * pix_square_size),
    #             width=3,
    #         )

    #     if self.render_mode == "human":
    #         self.window.blit(canvas, canvas.get_rect())
    #         pg.event.pump()
    #         pg.display.update()

    #         self.clock.tick(self.metadata["render_fps"])
    #     else:
    #         return np.transpose(
    #             np.array(pg.surfarray.pixels3d(canvas)), axes=(1, 0, 2)
    #         )
        
    # def close(self) -> None:
    #     super().close()
    #     if self.window is not None:
    #         pg.display.quit()
    #         pg.quit()
    
    # def get_target_states(self) -> List[Tuple[int, int]]:
    #     return dict((label, self.location_to_state(location)) for label, location in self._target_locations.items())

    # def location_to_state(self, location):
    #     return location[0] * self.size[0] + location[1]
    
    # def show(self):
    #    pass

class TFGridEnvGUI(PyGameGUI):

    #--------------------------------------------------------------    
    def __init__(self, sim, 
                 height=400, width=400,
                 cell_size=None,
                 fps=80,
                 batch_run=10000,
                 on_close_listeners:Iterable[Callable]=[],
                 close_on_finish=True):
                 
        super().__init__(sim,
                         height=height, width=width,
                         fps=fps, batch_run=batch_run,
                         on_close_listeners=on_close_listeners,
                         close_on_finish=close_on_finish)

        self.cell_size = cell_size


    #--------------------------------------------------------------    
    def launch(self, give_first_step=True, start_running=True):
       
        if self.cell_size is None:
            self.cell_size = self.height // self.sim.env.num_rows
            self.width = self.sim.env.num_cols * self.cell_size
        else:    
            # self.cell_size = cell_size
            self.height = self.sim.env.num_rows * self.cell_size
            self.width = self.sim.env.num_cols * self.cell_size
        
        self.margin_size = 10 
        self.board_height = self.sim.env.num_rows * self.cell_size
        self.board_width = self.sim.env.num_cols * self.cell_size
        
        self.height = 5 * (self.board_height + self.margin_size) + 2 * self.cell_size

        self.font_size = int(self.cell_size * 0.8)
        self.font = pg.font.SysFont(None, self.font_size)
        
        self.max_r = self.sim.env.reward_matrix.max()
        self.min_r = self.sim.env.reward_matrix.min()
        self.delta_r = self.max_r - self.min_r
        
        #define colors for reward matrix
        self.reward_color_matrix = np.zeros((self.sim.env.num_cols, self.sim.env.num_rows, 3), dtype=int)
        for x in range(self.sim.env.num_cols):
            for y in range(self.sim.env.num_rows):
                reward = self.sim.env.reward_matrix[x, y]
                if reward == 0:
                    r = g = b = 200
                elif reward < 0:
                    r = 255
                    g = int(255 * (1.0 - (reward / self.min_r)) / 1.5)
                    b = g
                else:
                    g = 255
                    r = int(255 * (1.0 - (reward / self.max_r)) / 1.5)
                    b = r
                self.reward_color_matrix[x, y] = [r, g, b]
                
        super().launch(give_first_step=give_first_step, start_running=start_running)
       
    #--------------------------------------------------------------    
    def _draw_grid(self, canvas, vertical_skip=None, vertical_position=0, line_color=(100, 100, 100)):

         if vertical_skip is None:
            vertical_skip = vertical_position * (self.board_height + self.margin_size)
         
         line_color = (0, 0, 0
                       )
         #draw horizontal lines
         for y in range(self.sim.env.num_rows + 1):
             pg.draw.line(
                 canvas,
                 line_color,
                 (0, self.cell_size * y + vertical_skip),
                 (self.board_width, self.cell_size * y + vertical_skip),
                 width=3,
             )

         #draw vertical lines
         for x in range(self.sim.env.num_cols + 1):
             pg.draw.line( 
                 canvas,
                 line_color,
                 (self.cell_size * x, vertical_skip),
                 (self.cell_size * x, vertical_skip + self.board_height),
                 width=3,
             )
       
    #--------------------------------------------------------------    
    def _draw_rewards(self, canvas, vertical_position=0):

         vertical_skip = vertical_position * (self.board_height + self.margin_size)
       
         #draw the rewards
         for x in range(self.sim.env.num_cols):
             for y in range(self.sim.env.num_rows):
                 pg.draw.rect(
                     canvas,
                     self.reward_color_matrix[x, y],
                     pg.Rect(
                         (self.cell_size * x, self.cell_size * y + vertical_skip),
                         (self.cell_size, self.cell_size),
                     ),
                 )
                 
         self._draw_grid(canvas, vertical_skip=vertical_skip)

    #--------------------------------------------------------------    
    def _draw_agent(self, canvas, vertical_skip=None, vertical_position=0, agent_color=(0, 0, 255)):

         if vertical_skip is None:
            vertical_skip = vertical_position * (self.board_height + self.margin_size)
       
         if hasattr(self.sim.agent, "recharge_mode") and self.sim.agent.recharge_mode:
             agent_color = (255, 255, 0)
             
         pg.draw.circle(
             canvas,
             agent_color,
             (self.sim.env._agent_location + 0.5 + [0, vertical_skip]) * self.cell_size,
             self.cell_size / 3,
         )

    #--------------------------------------------------------------    
    def _draw_agent_position(self, canvas, vertical_skip=None, vertical_position=0, color=(255, 255, 50)):

         if vertical_skip is None:
            vertical_skip = vertical_position * (self.board_height + self.margin_size)
       
         pg.draw.rect(
             canvas,
             color,
             pg.Rect(
                 self.sim.env._agent_location[0] * self.cell_size, self.sim.env._agent_location[1] * self.cell_size + vertical_skip,
                 self.cell_size, self.cell_size
             ),
             width=3
         )

      #--------------------------------------------------------------    
    def _color(self, v, min_v, amplitude_v, color_mode='grayscale'):
         c = int(255 * (v - min_v) / amplitude_v)
         if color_mode == 'inversed_grayscale':
            c = 255-c
         elif color_mode == 'log_grayscale':
            c = 255//(v+1)
         elif color_mode == 'inversed_log_grayscale':
            c = 255 - 255//(v+1)
         return c

    #--------------------------------------------------------------    
    def _draw_sa_matrix(self, canvas, matrix, min_q=None, max_q=None, vertical_skip=None, vertical_position=0, color_mode='grayscale', backcolor=None):
         
       if vertical_skip is None:
          vertical_skip = vertical_position * (self.board_height + self.margin_size)
       
       if max_q is None:
          max_q = matrix.max()
       
       if min_q is None:
          min_q = matrix.min()
       
       dif_q = max_q - min_q
       
       if max_q > min_q:
      
          for x in range(self.sim.env.num_cols):
             for y in range(self.sim.env.num_rows):
                   
                q = matrix[x, y].max()
                if backcolor is None:
                   c = self._color(q, min_q, dif_q, color_mode=color_mode)
                   color = (c, c, c)
                else:
                   color = backcolor
                points = pg.Rect(
                           (x * self.cell_size, y * self.cell_size + vertical_skip),
                           (self.cell_size, self.cell_size),
                       )
                pg.draw.rect(canvas, color, points)
                
                #0: np.array([1, 0]),  #right
                q = matrix[x, y, 0]
                c = self._color(q, min_q, dif_q, color_mode=color_mode)
                right_triangle_points = [
                     ((x+1) * self.cell_size, y * self.cell_size + self.cell_size//2 + vertical_skip), 
                     (x * self.cell_size + 2*self.cell_size//3, y * self.cell_size + self.cell_size//3 + vertical_skip), 
                     (x * self.cell_size + 2*self.cell_size//3, y * self.cell_size + 2*self.cell_size//3 + vertical_skip)
                  ]
                pg.draw.polygon(canvas, (c, c, c), right_triangle_points)
                pg.draw.polygon(canvas, (0, 0, 0), right_triangle_points, width=1)


                #1: np.array([0, 1]),  #down
                q = matrix[x, y, 1]
                c = self._color(q, min_q, dif_q, color_mode=color_mode)
                down_triangle_points = [
                       (x * self.cell_size + self.cell_size//2, (y+1) * self.cell_size + vertical_skip), 
                       (x * self.cell_size + self.cell_size//3,   y * self.cell_size + 2*self.cell_size//3 + vertical_skip), 
                       (x * self.cell_size + 2*self.cell_size//3, y * self.cell_size + 2*self.cell_size//3 + vertical_skip)
                     ]
                pg.draw.polygon(canvas, (c, c, c), down_triangle_points)
                pg.draw.polygon(canvas, (0, 0, 0), down_triangle_points, width=1)

                #2: np.array([-1, 0]), #left
                q = matrix[x, y, 2]
                c = self._color(q, min_q, dif_q, color_mode=color_mode)
                left_triangle_points = [
                       (x * self.cell_size, y * self.cell_size + self.cell_size//2 + vertical_skip), 
                       (x * self.cell_size + self.cell_size//3, y * self.cell_size + self.cell_size//3 + vertical_skip), 
                       (x * self.cell_size + self.cell_size//3, y * self.cell_size + 2*self.cell_size//3 + vertical_skip)
                     ]
                pg.draw.polygon(canvas, (c, c, c), left_triangle_points)
                pg.draw.polygon(canvas, (0, 0, 0), left_triangle_points, width=1)
                   
                #3: np.array([0, -1]), #up                
                q = matrix[x, y, 3]
                c = self._color(q, min_q, dif_q, color_mode=color_mode)
                up_triangle_points = [
                       (x * self.cell_size + self.cell_size//2, y * self.cell_size + vertical_skip), 
                       (x * self.cell_size + self.cell_size//3,   y * self.cell_size + self.cell_size//3 + vertical_skip), 
                       (x * self.cell_size + 2*self.cell_size//3, y * self.cell_size + self.cell_size//3 + vertical_skip)
                     ]
                pg.draw.polygon(canvas, (c, c, c), up_triangle_points)
                pg.draw.polygon(canvas, (0, 0, 0), up_triangle_points, width=1)
                
       #draw grid lines
       self._draw_grid(canvas, vertical_skip=vertical_skip)
       self._draw_agent_position(canvas, vertical_skip=vertical_skip)
       
       
    #--------------------------------------------------------------    
    def _draw_bar(self, canvas, v, max_v, vertical_skip=None, vertical_position=0, bar_position=0, color=(50, 50, 200) ):

       if vertical_skip is None:
          vertical_skip = vertical_position * (self.board_height + self.margin_size) + bar_position * self.cell_size

       points = pg.Rect(
                    (0, vertical_skip),
                    (int(self.width * (v / max_v)), self.cell_size),
                  )
       
       pg.draw.rect(canvas, color, points)

    #--------------------------------------------------------------    
    def _draw_bar_label(self, label, vertical_skip=None, vertical_position=0, bar_position=0, color=(0, 0, 0) ):

       if vertical_skip is None:
          vertical_skip = vertical_position * (self.board_height + self.margin_size) + bar_position * self.cell_size

       img =   self.font.render(str(label), True, color)
       self.window.blit(img, (20, vertical_skip+10))

    #--------------------------------------------------------------    
    def refresh(self):

         #clear canvas
         canvas = pg.Surface((self.width, self.height))
         canvas.fill((255, 255, 255))

         #draw the rewards
         self._draw_rewards(canvas, vertical_position=0)
         
         #draw the agent
         self._draw_agent(canvas, vertical_position=0)

         #draw 1/(N+1) Matrix
         #self._draw_exploration(canvas, vertical_position=1)
         if hasattr(self.sim.agent, 'N') and self.sim.agent.N is not None:
            self._draw_sa_matrix(canvas, matrix=self.sim.agent.N, vertical_position=1, min_q=0, color_mode='inversed_log_grayscale')
                    
         #draw Q Matrix
         if hasattr(self.sim.agent, 'Q') and self.sim.agent.Q is not None:
            self._draw_sa_matrix(canvas, matrix=self.sim.agent.Q, vertical_position=2)

         #draw K Matrix
         if hasattr(self.sim.agent, 'K') and self.sim.agent.K is not None:
            self._draw_sa_matrix(canvas, matrix=self.sim.agent.K, vertical_position=3)

         #draw Policy
         if hasattr(self.sim.agent, 'policy') and self.sim.agent.policy is not None:
            self._draw_sa_matrix(canvas, matrix=self.sim.agent.policy, vertical_position=4, min_q=0, backcolor=(0,0,0))

         #budget bar
         if hasattr(self.sim.agent, "b") and self.sim.agent.b is not None:
            self._draw_bar(canvas, v=self.sim.agent.b, max_v=1000, vertical_position=5, bar_position=0)

         #time bar
         self._draw_bar(canvas, v=self.sim.t, max_v=self.sim.episode_horizon, vertical_position=5, bar_position=1, color=(0,150,0))
         
         #canvas
         self.window.blit(canvas, canvas.get_rect())

         #time label
         self._draw_bar_label("t = " + str(self.sim.env.t), vertical_position=5, bar_position=1)

         #budget label
         if hasattr(self.sim.agent, "b") and self.sim.agent.b is not None:
             #budget_color = (200, 0, 0) if self.sim.agent.b < 0 else (0, 200, 0)
             self._draw_bar_label("b = " + str(self.sim.agent.b), vertical_position=5, bar_position=0)

         #refresh
         #pg.display.update()
         
         ###self.clock.tick(self.fps)
         
         super().refresh()






        
# class GridEnvRender():

#     def __init__(self, env, agent=None, fps=40, height=None, width=None, cell_size=None,
#                  interruption_callback:Callable=None):

#         self.env = env       #reference to the environment
#         self.agent = agent   #reference to the active agent
        
#         if cell_size is None:
#             if height is None: 
#                 if width is None:
#                     self.height = 600
#                     self.cell_size = self.height // self.env.num_rows
#                     self.width = self.env.num_cols * self.cell_size
#                 else:
#                     self.width = width
#                     self.cell_size = self.width // self.env.num_cols
#                     self.height = self.env.num_rows * self.cell_size
#             else: 
#                 if width is None:
#                     self.height = height
#                     self.cell_size = self.height // self.env.num_rows
#                     self.width = self.env.num_cols * self.cell_size
#                 else:
#                     self.width = width
#                     self.cell_size = self.width // self.env.num_cols
#                     self.height = self.env.num_rows * self.cell_size
#         else:    
#             self.cell_size = cell_size
#             self.height = self.env.num_rows * self.cell_size
#             self.width = self.env.num_cols * self.cell_size
        
#         self.board_height = self.env.num_rows * self.cell_size + 10
#         self.board_width = self.env.num_cols * self.cell_size
        
#         self.height = 3 * self.board_height + 50
        
#         self.fps = fps
        
#         self.window = None
#         self.clock = None
        
#         pg.init()
#         pg.display.init()
#         self.window = pg.display.set_mode( (self.width, self.height) )
#         self.clock = pg.time.Clock()
        
#         self.font_size = int(self.cell_size * 0.8)
#         self.font = pg.font.SysFont(None, self.font_size)
        
#         self.max_r = self.env.reward_matrix.max()
#         self.min_r = self.env.reward_matrix.min()
#         self.delta_r = self.max_r - self.min_r
        
#         #define colors for reward matrix
#         self.color_matrix = np.zeros((self.env.num_cols, self.env.num_rows, 3), dtype=int)
#         for x in range(self.env.num_cols):
#             for y in range(self.env.num_rows):
#                 reward = self.env.reward_matrix[x, y]
#                 if reward == 0:
#                     r = g = b = 200
#                 elif reward < 0:
#                     r = 255
#                     g = int(255 * (1.0 - (reward / self.min_r)) / 1.5)
#                     b = g
#                 else:
#                     g = 255
#                     r = int(255 * (1.0 - (reward / self.max_r)) / 1.5)
#                     b = r
#                 self.color_matrix[x, y] = [r, g, b]

#     def refresh(self):

#         if self.env.interrupted:
            
#             self.clock.tick(0)
#             self.close()

#         else:

#             events = pg.event.get()
#             for event in events:
#                if event.type == pg.QUIT:
#                    self.env.interrupted = True
           
#             #clear canvas
#             canvas = pg.Surface((self.width, self.height))
#             canvas.fill((255, 255, 255))


#             #draw the rewards
#             for x in range(self.env.num_cols):
#                 for y in range(self.env.num_rows):
#                     pg.draw.rect(
#                         canvas,
#                         self.color_matrix[x, y],
#                         pg.Rect(
#                             self.cell_size * np.array([x, y]),
#                             (self.cell_size, self.cell_size),
#                         ),
#                     )
            
#             #draw the agent
#             agent_color = (0, 0, 255)
#             if (self.agent is not None) and hasattr(self.agent, "recharge_mode") and self.agent.recharge_mode:
#                 agent_color = (255, 255, 0)
#             pg.draw.circle(
#                 canvas,
#                 agent_color,
#                 (self.env._agent_location + 0.5) * self.cell_size,
#                 self.cell_size / 3,
#             )

#             #draw horizontal lines
#             for y in range(self.env.num_rows + 1):
#                 pg.draw.line(
#                     canvas,
#                     (0, 0, 0),
#                     (0, self.cell_size * y),
#                     (self.board_width, self.cell_size * y),
#                     width=3,
#                 )

#             #draw vertical lines
#             for x in range(self.env.num_cols + 1):
#                 pg.draw.line(
#                     canvas,
#                     (0, 0, 0),
#                     (self.cell_size * x, 0),
#                     (self.cell_size * x, self.board_height),
#                     width=3,
#                 )

#             #draw 1/(N+1) Matrix
#             if hasattr(self.agent, 'N') and self.agent.N is not None:
#                for x in range(self.env.num_cols):
#                    for y in range(self.env.num_rows):
#                     #    print((x,y))
#                        n_min = 255 - 255//(self.agent.N[x, y].min()+1) 
#                        n_max = 255 - 255//(self.agent.N[x, y].max()+1) 
#                        pg.draw.rect(
#                            canvas,
#                            (n_min, n_min, n_min),
#                            pg.Rect(
#                                (x * self.cell_size, y * self.cell_size + self.board_height),
#                                (self.cell_size, self.cell_size),
#                            )
#                        )
#                        pg.draw.circle(
#                            canvas,
#                            (n_max, n_max, n_max),
#                            ((x+0.5) * self.cell_size, (y+0.5) * self.cell_size + self.board_height),
#                            self.cell_size / 4,
#                        )
                       
            
#             #draw horizontal lines
#             for y in range(self.env.num_rows + 1):
#                 pg.draw.line(
#                     canvas,
#                     (100, 100, 100),
#                     (0, self.cell_size * y + self.board_height),
#                     (self.board_width, self.cell_size * y + self.board_height),
#                     width=3,
#                 )

#             #draw vertical lines
#             for x in range(self.env.num_cols + 1):
#                 pg.draw.line(
#                     canvas,
#                     (100, 100, 100),
#                     (self.cell_size * x, self.board_height),
#                     (self.cell_size * x, 2 * self.board_height),
#                     width=3,
#                 )

#             #draw Q Matrix
#             if hasattr(self.agent, 'Q') and self.agent.Q is not None:
#                max_q = self.agent.Q.max()
#                min_q = self.agent.Q.min()
#                if max_q > min_q:
#                   for x in range(self.env.num_cols):
#                       for y in range(self.env.num_rows):
#                         #   q = self.agent.Q[x, y].max()
#                           q = self.agent.Q[y][x]
#                           c = int(255 * (q - min_q) / (max_q - min_q))
#                           pg.draw.rect(
#                               canvas,
#                               (c, c, c),
#                               pg.Rect(
#                                   (x * self.cell_size, y * self.cell_size + 2*self.board_height),
#                                   (self.cell_size, self.cell_size),
#                               )
#                           )
                          
#             #draw horizontal lines
#             for y in range(self.env.num_rows + 1):
#                 pg.draw.line(
#                     canvas,
#                     (100, 100, 100),
#                     (0, self.cell_size * y + 2 * self.board_height),
#                     (self.board_width, self.cell_size * y + 2 * self.board_height),
#                     width=3,
#                 )

#             #draw vertical lines
#             for x in range(self.env.num_cols + 1):
#                 pg.draw.line(
#                     canvas,
#                     (100, 100, 100),
#                     (self.cell_size * x, 2 * self.board_height),
#                     (self.cell_size * x, 3 * self.board_height),
#                     width=3,
#                 )

#             #budget bar
#             if (self.agent is not None) and hasattr(self.agent, "b") and self.agent.b is not None:
#                 pg.draw.rect(
#                    canvas,
#                    (50, 50, 200),
#                    pg.Rect(
#                        (0, 3*self.board_height+30),
#                        ( int(self.width * (self.agent.b / 1000)), self.cell_size),
#                    )
#                 )

#             #canvas
#             self.window.blit(canvas, canvas.get_rect())

#             #time
#             img_time =   self.font.render(str(self.env.t), True, (0,0,0))
#             self.window.blit(img_time, (20, 3*self.board_height+10))

#             #budget
#             if (self.agent is not None) and hasattr(self.agent, "b") and self.agent.b is not None:
#                 budget_color = (200, 0, 0) if self.agent.b < 0 else (0, 200, 0)
#                 img_budget = self.font.render(str(self.agent.b), True, budget_color)
#                 self.window.blit(img_budget, (20, 3*self.board_height+30))
#             else:
#                 budget_color = (200, 0, 0)
#                 img_budget = self.font.render('None', True, budget_color)
#                 self.window.blit(img_budget, (20, 3*self.board_height+30))

#             #refresh
#             pg.display.update()
#             self.clock.tick(self.fps)
                
        
#     def close(self) -> None:
#         if self.window is not None:
#             pg.display.quit()
#             pg.quit()
