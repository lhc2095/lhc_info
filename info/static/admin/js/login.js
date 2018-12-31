function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 管理员用户登录表单提交  ---------------------------
$(function () {
    $(".login_form").submit(function (e) {
        e.preventDefault()
    var user_name=$(".login_form #username").val();
    var password=$(".login_form #password").val();
    var params={
        "username":user_name,
        "password":password
    }
    $.ajax({
        url:'/admin/login_in',
        data:JSON.stringify(params),
        contentType:"application/json",
        type:'post',
        headers:{
                'X-CSRFToken':getCookie("csrf_token")
            },
        success:function (resp) {
            if  (resp.errno == "0"){
                var url='index';
                alert('hello')
                location.href='index'
            }else {
                location.reload();
                alert(resp.errmsg)
            }
        }
    })
    })
})