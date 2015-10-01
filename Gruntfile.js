'use strict';

module.exports = function(grunt) {
    grunt.initConfig({
        rsync: {
            options: {
                args: ['-avz', '--verbose', '--delete'],
                recursive: true
            },
            prod: {
                options: {
                    // the dir you want to sync, in this case the current dir
                    src: './site/_site/',
                    // where should it be synced to on the remote host?
                    dest: '~/public_html/bugnotes/',
                    // what's the creds and host
                    host: 'mconley2@people.mozilla.com'
                }
            }
        }
    });

    grunt.loadNpmTasks('grunt-rsync');

    grunt.registerTask('deploy', ['rsync:prod']);
};

