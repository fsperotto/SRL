from gymnasium.envs.registration import register
from .survival import SurvivalEnv
#from .tensorforce_survival import CustomEnvironment
from .simple_survival import SimpleSurvivalEnv
#from .tf_grid import TFGridEnv, TFGridEnvGUI

register(
    id="Survival-v0",
    entry_point="pyrl.environments:SurvivalEnv",
)

register(
    id="SimpleSurvival-v0",
    entry_point="pyrl.environments:SimpleSurvivalEnv",
)