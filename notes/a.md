Its clear that we, as in we humans, do not understand how these black boxes work. Like the human brain they are made to mimic, we are not even close to understanding its capabilities.

AIs are better at write code than calling tools.


# TODO:

- [ ] Research
    - [ ] scheming behaviour in LLMs
    - [ ] how llms behave when asked difficult questions
    - [ ] how has game theory been tested
    - [ ] how was their CoT analysed
    - [ ] testing conditions for these tests
    - [ ] which tests would be thes most effective and doable in the limited time frame

- [ ] Implementation
    - [ ] Create a python project which integrates with Langchain to create agents along with configurable prompts.
    - [ ] be able to integrate with differnt APIs,
    - [ ] add extensive logging mechanism to aid evaluation
    - [ ] create test realistic senarios.
    - [ ] rent GPUs for open source models to test their reasonings
    - [ ] implement the variables during testing for each model.

- [ ] Evaluation
    Need an evaultion critera. it could be differnet variables that we change and compare how the models behave. For example, the variable can be observability, if the agent thinks its being monitored vs when the agent thinks its not . 
    - [ ] potential variables:
        - [ ] Observability
        - [ ] how high the conseqences will be (maybe low-mid-high)
        - [ ] how realistic the senario is ?? (less-high)
        - [ ] reasoning or not
