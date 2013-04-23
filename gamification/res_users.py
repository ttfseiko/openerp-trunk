from openerp.osv import osv


class res_users_gamification_group(osv.Model):
    """ Update of res.users class
        - if adding groups to an user, check gamification.goal.plan linked to
        this group, and the user. This is done by overriding the write method.
    """
    _name = 'res.users'
    _inherit = ['res.users']

    def write(self, cr, uid, ids, vals, context=None):
        write_res = super(res_users_gamification_group, self).write(cr, uid, ids, vals, context=context)
        if vals.get('groups_id'):
            # form: {'group_ids': [(3, 10), (3, 3), (4, 10), (4, 3)]} or {'group_ids': [(6, 0, [ids]}
            user_group_ids = [command[1] for command in vals['groups_id'] if command[0] == 4]
            user_group_ids += [id for command in vals['groups_id'] if command[0] == 6 for id in command[2]]

            goal_plan_obj = self.pool.get('gamification.goal.plan')
            plan_ids = goal_plan_obj.search(cr, uid, [('autojoin_group_id', 'in', user_group_ids)], context=context)
            if plan_ids:
                goal_plan_obj.write(cr, uid, plan_ids, {'user_ids': [(4, user_id) for user_id in ids]}, context=context)

        if vals.get('image'):
            self.pool.get('gamification.goal').changed_users_avatar(cr, uid, ids, context)
        return write_res

    def get_goals_todo_info(self, cr, uid, context=None):
        """Return the list of goals assigned to the user, grouped by plan"""
        all_goals_info = []
        plan_obj = self.pool.get('gamification.goal.plan')

        plan_ids = plan_obj.search(cr, uid, [('user_ids', 'in', uid), ('state', '=', 'inprogress')], context=context)
        for plan in plan_obj.browse(cr, uid, plan_ids, context=context):
            # serialize goals info to be able to use it in javascript
            serialized_goals_info = {
                'id': plan.id,
                'name': plan.name,
                'visibility_mode': plan.visibility_mode,
            }
            user = self.browse(cr, uid, uid, context=context)
            serialized_goals_info['currency'] = user.company_id.currency_id.id

            if plan.visibility_mode == 'board':
                # board report should be grouped by planline for all users
                goals_info = plan_obj.get_board_goal_info(cr, uid, plan, subset_goal_ids=False, context=context)

                if len(goals_info) == 0:
                    # plan with no valid planlines
                    continue

                serialized_goals_info['planlines'] = []
                for planline_board in goals_info:
                    vals = {'type_name': planline_board['goal_type'].name,
                            'type_description': planline_board['goal_type'].description,
                            'type_condition': planline_board['goal_type'].condition,
                            'type_computation_mode': planline_board['goal_type'].computation_mode,
                            'type_monetary': planline_board['goal_type'].monetary,
                            'type_unit': planline_board['goal_type'].unit,
                            'type_action': True if planline_board['goal_type'].action_id else False,
                            'type_display': planline_board['goal_type'].display_mode,
                            'target_goal': planline_board['target_goal'],
                            'goals': []}
                    for goal in planline_board['board_goals']:
                        # Keep only the Top 3 and the current user
                        if goal[0] > 2 and goal[1].user_id.id != uid:
                            continue

                        vals['goals'].append({
                            'rank': goal[0]+1,
                            'id': goal[1].id,
                            'user_id': goal[1].user_id.id,
                            'user_name': goal[1].user_id.name,
                            'state': goal[1].state,
                            'completeness': goal[1].completeness,
                            'current': goal[1].current,
                            'target_goal': goal[1].target_goal,
                        })
                        if uid == goal[1].user_id.id:
                            vals['own_goal_id'] = goal[1].id
                    serialized_goals_info['planlines'].append(vals)

            else:
                # individual report are simply a list of goal
                goals_info = plan_obj.get_indivual_goal_info(cr, uid, uid, plan, subset_goal_ids=False, context=context)

                if not goals_info:
                    continue

                serialized_goals_info['goals'] = []
                for goal in goals_info['goals']:
                    serialized_goals_info['goals'].append({
                        'id': goal.id,
                        'type_name': goal.type_id.name,
                        'type_description': goal.type_description,
                        'type_condition': goal.type_id.condition,
                        'type_monetary': goal.type_id.monetary,
                        'type_unit': goal.type_id.unit,
                        'type_action': True if goal.type_id.action_id else False,
                        'type_display': goal.type_id.display_mode,
                        'state': goal.state,
                        'completeness': goal.completeness,
                        'computation_mode': goal.computation_mode,
                        'current': goal.current,
                        'target_goal': goal.target_goal,
                    })

            all_goals_info.append(serialized_goals_info)
        return all_goals_info

    def get_challenge_suggestions(self, cr, uid, context=None):
        """Return the list of goal plans suggested to the user"""
        if context is None: context = {}
        plan_info = []
        plan_ids = self.pool.get('gamification.goal.plan').search(cr, uid, [('proposed_user_ids', 'in', uid), ('state', '=', 'inprogress')], context=context)
        for plan in self.pool.get('gamification.goal.plan').browse(cr, uid, plan_ids, context=context):
            values = {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
            }
            plan_info.append(values)
        return plan_info


class res_groups_gamification_group(osv.Model):
    """ Update of res.groups class
        - if adding users from a group, check gamification.goal.plan linked to
        this group, and the user. This is done by overriding the write method.
    """
    _name = 'res.groups'
    _inherit = 'res.groups'

    def write(self, cr, uid, ids, vals, context=None):
        write_res = super(res_groups_gamification_group, self).write(cr, uid, ids, vals, context=context)
        if vals.get('users'):
            # form: {'group_ids': [(3, 10), (3, 3), (4, 10), (4, 3)]} or {'group_ids': [(6, 0, [ids]}
            user_ids = [command[1] for command in vals['users'] if command[0] == 4]
            user_ids += [id for command in vals['users'] if command[0] == 6 for id in command[2]]

            goal_plan_obj = self.pool.get('gamification.goal.plan')
            plan_ids = goal_plan_obj.search(cr, uid, [('autojoin_group_id', 'in', ids)], context=context)
            if plan_ids:
                goal_plan_obj.write(cr, uid, plan_ids, {'user_ids': [(4, user_id) for user_id in user_ids]}, context=context)
        return write_res
