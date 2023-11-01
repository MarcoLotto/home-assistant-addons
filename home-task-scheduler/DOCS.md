# Home Assistant Add-on: Home Task Scheduler

The Home Task Scheduler add-on allows you to schedule daily household tasks and evenly distribute them among the house members.

## Tasks and Users Configuration

1. **Setup**: Import the repository and install the add-on. Once installed and started, use a File editor in Home Assistant to navigate to the `config` folder. Here, you'll find the `home-task-scheduler` folder, which contains:
    - `tasks.yaml`
    - `user.yaml`
    - `database.db`

2. **Configuring Tasks (`tasks.yaml`)**:
    - The file already contains example tasks. Feel free to add, modify, or remove them.
    - Ensure that each task ID is unique.
    - Task properties include:
        - `id`: A unique numeric identifier.
        - `name`: Task description.
        - `days_interval`: Interval in days before re-scheduling.
        - `effort`: Effort points the task consumes.
        - `allowed_days` (optional): Specific days for the task.

    Example:
    ```yaml
    - id: 1
      name: Clean the kitchen
      days_interval: 3
      effort: 1
    ```
    That is meant to be a simple task (low effort), and should be scheduled every three days

    Here's a more intricate example:
    ```yaml
    - id: 5
      name: Take out trash
      days_interval: 2
      effort: 0
      allowed_days:
        - mon
        - tue
        - wed
        - thu
        - fri
    ```
    This task will be scheduled only on week days, every 2 days, and with zero effort, which means, even if the users do not have enough effort points available, it will be scheduled anyway as it needs to be done.

3. **Configuring Users (`user.yaml`)**:
    - You can add, modify, or remove users. Ensure that user IDs remain unique.
    - Allocate daily effort points for each user.

    Example:
    ```yaml
    - id: 1
      username: Marco
      available_daily_effort:
        mon: 3
        tue: 2
        wed: 3
        thu: 3
        fri: 3
        sat: 4
        sun: 4
    ```
    This user will be assigned with more time-consuming tasks on Sundays than on Tuesdays for example.

4. **Data File (`database.db`)**: Contains application-generated data. If you've altered task IDs significantly, consider deleting this file and starting afresh. If deleted, restart the add-on to regenerate. Modifications to YAML files don't require a restart—they're read dynamically.

## Building Sensors for Automations

The add-on exposes a local server on port 8000. To craft automations, interact with this server.

In `configuration.yaml` on Home Assistant, append:

```yaml
sensor:
  - platform: rest
    name: "Home Pending Tasks"
    resource: http://localhost:8000/notifications/scheduled-tasks?language=en
    value_template: '{{ value_json.notification_available }}'
    json_attributes:
      - notification_available
      - notification_message
      
rest_command:
  complete_home_tasks_marco:
    url: http://localhost:8000/users/1/pending-tasks
    method: PUT
    headers:
      content-type: 'application/json'
    payload: '{"status": "completed"}'
  complete_home_tasks_mayra:
    url: http://localhost:8000/users/2/pending-tasks
    method: PUT
    headers:
      content-type: 'application/json'
    payload: '{"status": "completed"}'
```

This configuration enables a sensor to detect scheduled tasks and offers a mechanism to inform the server about task completions. 
On the tasks sensor, notice that a language can be provided, currently it can be "en" or "es". Also on the json_attibutes there is the notification_message. That attribute will contain a message which can be displayed on automations (like the ones described below). 
There also are more endpoints available to fine-tune the task management, use them as you consider.

## Example Automations

### Notification of Tasks on Media Player

Announce the day's pending tasks on a media player. Adjust the language by setting it to either "es" (Spanish) or "en" (English).

```yaml
alias: Announce Pending Tasks
description: Announces the day's tasks on the media player.
trigger:
  - platform: time_pattern
    seconds: "0"
    minutes: "10"
condition:
  - condition: state
    entity_id: sensor.home_pending_tasks
    state: "True"
    for:
      hours: 0
      minutes: 0
      seconds: 10
  - condition: time
    after: "10:00:00"
    before: "23:00:00"
action:
  - service: media_player.volume_set
    data:
      volume_level: 0.65
    target:
      entity_id: media_player.living
  - service: tts.speak
    data:
      cache: true
      media_player_entity_id: media_player.living
      message: >-
        {% set message = state_attr('sensor.home_pending_tasks',
        'notification_message') %} Home Tasks: {{ message }}
      language: en
    target:
      entity_id: tts.google_en_com
mode: single
```

## Example Dashbord cards

## User task completion button

```yaml
show_name: true
show_icon: true
type: button
tap_action:
  action: call-service
  service: rest_command.complete_home_tasks_marco
  target: {}
name: Marco - Complete Home Tasks
icon: mdi:home-clock
icon_height: 100px
```

## Markdown card with pending tasks

```yaml
type: markdown
content: |-
  {% set message = state_attr('sensor.home_pending_tasks',
      'notification_message') %} {{ message }}
title: Home Tasks
```