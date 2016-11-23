# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Flask, jsonify, render_template
from flask_restful import Resource, Api, reqparse
from . import guiltypatches


app = Flask(__name__, template_folder='../templates', static_folder='../html', static_url_path='')
api = Api(app)


class Patches(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('channel', type=str, default='')
        parser.add_argument('product', type=str, default='')
        parser.add_argument('date', type=str, default='')
        args = parser.parse_args()
        if not (args.channel and args.product and args.date):
            return jsonify(guiltypatches.getinfos())
        else:
            return jsonify(guiltypatches.get(args.channel, args.product, args.date))


api.add_resource(Patches, '/rest/patches', endpoint='patches')


@app.route('/patches')
def patches_html():
    parser = reqparse.RequestParser()
    parser.add_argument('channel', type=str, default='nightly')
    parser.add_argument('product', type=str, default='Firefox')
    parser.add_argument('date', type=str, default='')
    args = parser.parse_args()

    channel, product, date = guiltypatches.check_args(args.channel, args.product, args.date)
    infos = guiltypatches.getinfos()
    if date is None:
        date = ''

    return render_template('patches.html', channel=channel, product=product, date=date, infos=infos)


if __name__ == '__main__':
    app.run()
