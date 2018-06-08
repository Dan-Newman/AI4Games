import copy
class GOAP_State:
    def __init__(self, states):
        self.states ={}
        for state in states:
            self.add_state(state)

    def add_state(self, name, value = False):
            self.states[name] = value

    def preconditions_met(self, action):
        for precondition in action.preconditions:
            if self.states[precondition['State']] != precondition['Needed']:
                return False
        return True

    def perform_action(self, action):
        for effect in action.effects:
            self.states[effect['State']] += effect['Result']

class GOAP_Action():
    def __init__(self, name, cost):
        self.name = name
        self.cost = cost
        self.preconditions = []
        self.effects = []

    def add_precondition(self, precondition, value = True):
        self.preconditions.append({'State':precondition, 'Needed': value})

    def add_effect(self, effect, value = True):
        self.effects.append({'State': effect,'Result': value})

class GOAP_Agent:
    def __init__(self):
        self.state = []
        self.actions = []
        self.running_cost = 0

        self.paths_evaluated = 0


    def perform_action(self, action):
        self.state.perform_action(action)
        self.running_cost += action.cost

    def plan(self, goal, state = None, path = None, start_action = None):

        if state is None:
            state = copy.deepcopy(self.state)

        if path is None:
            path = {'Actions': [], 'Cost': 0}
            self.paths_evaluated = 0

        if start_action:
            path['Actions'].append(start_action)
            path['Cost'] += start_action.cost
            state.perform_action(start_action)

        if state.states[goal_state]:
            self.paths_evaluated += 1
            return path

        available_actions = set()
        for action in self.actions:
            if state.preconditions_met(action):
                available_actions.add(action)


        cheapest_path = None
        for action in available_actions:
            potential_path = self.plan(goal_state, copy.deepcopy(state), copy.deepcopy(path), action)

        if not cheapest_path or potential_path['Cost'] < cheapest_path['Cost']:
            cheapest_path = potential_path

        return cheapest_path


bake_bread = GOAP_Action('bake bread', 10)
get_flour = GOAP_Action('get flour', 5)
deliver_bread = GOAP_Action('deliver bread', 25)

agent = GOAP_Agent()
agent.state = GOAP_State(
    [
        'HasFlour',
        'HasBread',
        'DoJob'
    ])
agent.actions = [
    bake_bread,
    get_flour,
    deliver_bread
]

get_flour.add_precondition('HasFlour', False)
get_flour.add_effect('HasFlour')
bake_bread.add_precondition('HasFlour')
bake_bread.add_precondition('HasBread', False)
bake_bread.add_effect('HasBread')
deliver_bread.add_precondition('HasBread')
deliver_bread.add_precondition('DoJob', False)
deliver_bread.add_effect('DoJob')




goal_state = 'DoJob'
path = agent.plan(goal_state)

print ('Goal: ' + goal_state + "\n")
for i in range(len((path['Actions']))):
    print(str(i+1) + ') ' + path['Actions'][i].name + ' (' + str(path['Actions'][i].cost) + ')')

print ('Total cost: ' + str(path['Cost']))
input ("Press any key to continue")